"""Measure a creative's images or video frames with code, so the analysis does not have to guess.

  python tools/measure.py <run>/media/<id> [--pack <pack image>] [--hindi]

Reads frames.json (video, from frames.py) or every image in the folder, and writes
<folder>/measures.json:
- text: every line of on-creative text (OCR) with its box (0-1 of the width/height), confidence,
  and contrast ratio against its background (WCAG; 4.5 = easy to read, 3 = minimum for large text)
- text_area_pct: share of the frame covered by text boxes
- safe_zone (9:16 only): text inside Meta's Reels/Stories margins (top 14 %, bottom 35 %, sides 6 %)
- faces: face boxes and size (% of the frame)
- colours: 5 main colours with their share
- pack (with --pack): whether the product pack is in the frame, its box and size (feature matching)
- summary: first time text, a face and the pack appear (video), and frame counts
--hindi also reads Devanagari (Hindi, Marathi) and keeps the more confident reading of each line.
Needs: pip install rapidocr onnxruntime opencv-python-headless. The face model (YuNet, 0.2 MB) is
downloaded once into tools/models/; without it faces are "not measured" (null) and judged by eye
(OpenCV's older Haar detector was tested and invented faces in ads without people).
"""
import argparse, hashlib, json, sys, urllib.request
from pathlib import Path

import cv2
import numpy as np

MODELS = Path(__file__).resolve().parent / "models"
YUNET = ("face_detection_yunet_2023mar.onnx",
         "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
         "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4")
SAFE = {"top": 0.14, "bottom": 0.35, "side": 0.06}  # Meta 9:16 safe zone (Reels, the tightest placement)
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def model_file(name, url, sha256):
    path = MODELS / name
    if not path.exists():
        try:
            MODELS.mkdir(exist_ok=True)
            data = urllib.request.urlopen(url, timeout=60).read()
            if hashlib.sha256(data).hexdigest() != sha256:
                return None
            path.write_bytes(data)
        except OSError:
            return None
    return path


# ---------- OCR ----------
def ocr_engines(hindi):
    import logging
    logging.disable(logging.WARNING)  # RapidOCR's info/warning lines on stderr read as errors in PowerShell
    from rapidocr import RapidOCR, LangRec, ModelType, OCRVersion
    engines = [RapidOCR()]
    if hindi:
        engines.append(RapidOCR(params={"Rec.lang_type": LangRec.DEVANAGARI, "Rec.ocr_version": OCRVersion.PPOCRV5,
                                        "Rec.model_type": ModelType.MOBILE}))
    return engines


def iou(a, b):
    x0, y0, x1, y1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, x1 - x0) * max(0, y1 - y0)
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union else 0


def read_text(engines, img):
    h, w = img.shape[:2]
    lines = []
    for engine in engines:
        r = engine(img)
        for box, text, score in zip(r.boxes if r.boxes is not None else [], r.txts or [], r.scores or []):
            if score < 0.5 or not any(ch.isalnum() for ch in text):  # specks and stray symbols are not text
                continue
            xs, ys = [p[0] for p in box], [p[1] for p in box]
            b = [max(min(xs) / w, 0), max(min(ys) / h, 0), min(max(xs) / w, 1), min(max(ys) / h, 1)]
            if score < 0.7 and b[3] - b[1] > 0.2:  # unsure "line" taller than 20% of frame: pattern or light, not text
                continue
            if sum(ch.isalnum() for ch in text) <= 2 and (b[2] - b[0]) * (b[3] - b[1]) > 0.15:  # 1-2 glyphs over 15% of the frame: a face, pattern or shape
                continue
            text = "".join(ch for ch in text if not "\u4e00" <= ch <= "\u9fff").strip()  # CJK glyphs from the Latin reader are misread icons
            if not any(ch.isalnum() for ch in text):
                continue
            same = next((l for l in lines if iou(l["box"], b) > 0.5), None)
            if same is None:
                lines.append({"text": text, "score": round(float(score), 2), "box": [round(float(v), 3) for v in b]})
            elif score > same["score"]:  # two readers on the same line: keep the more confident one
                same.update(text=text, score=round(float(score), 2))
    return lines


def luminance(rgb):
    c = np.asarray(rgb, float) / 255
    c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(img, box):
    h, w = img.shape[:2]
    crop = img[int(box[1] * h):int(box[3] * h) + 1, int(box[0] * w):int(box[2] * w) + 1]
    if crop.size < 12:
        return None
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    a, b = crop[mask > 0], crop[mask == 0]
    if not len(a) or not len(b):
        return None
    la, lb = luminance(a.mean(0)[::-1]), luminance(b.mean(0)[::-1])
    return round(float((max(la, lb) + 0.05) / (min(la, lb) + 0.05)), 1)


def text_area(lines):
    mask = np.zeros((200, 200), np.uint8)
    for l in lines:
        x0, y0, x1, y1 = (int(v * 200) for v in l["box"])
        mask[y0:y1, x0:x1] = 1
    return round(float(mask.mean()) * 100, 1)


def safe_zone(lines, w, h):
    if abs(w / h - 9 / 16) > 0.03:
        return None
    out = []
    for l in lines:
        x0, y0, x1, y1 = l["box"]
        zones = [z for z, hit in (("top", y0 < SAFE["top"]), ("bottom", y1 > 1 - SAFE["bottom"]),
                                  ("side", x0 < SAFE["side"] or x1 > 1 - SAFE["side"])) if hit]
        if zones:
            out.append({"text": l["text"], "zones": zones})
    return out


# ---------- faces ----------
class Faces:
    def __init__(self):
        path = model_file(*YUNET)
        self.kind = "yunet" if path else "not measured (face model could not be downloaded)"
        self.yunet = cv2.FaceDetectorYN.create(str(path), "", (320, 320), 0.8) if path else None

    def __call__(self, img):
        if self.yunet is None:
            return None
        h, w = img.shape[:2]
        self.yunet.setInputSize((w, h))
        _, found = self.yunet.detect(img)
        boxes = [] if found is None else [(f[0], f[1], f[2], f[3]) for f in found]
        return [{"box": [round(float(v), 3) for v in (x / w, y / h, (x + bw) / w, (y + bh) / h)],
                 "size_pct": round(float(bw * bh / (w * h) * 100), 1)} for x, y, bw, bh in boxes]


# ---------- colours ----------
def colours(img, k=5):
    small = cv2.resize(img, (64, 64), interpolation=cv2.INTER_AREA).reshape(-1, 3).astype(np.float32)
    _, labels, centres = cv2.kmeans(small, k, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1),
                                    3, cv2.KMEANS_PP_CENTERS)
    share = np.bincount(labels.ravel(), minlength=k) / len(labels)
    order = np.argsort(-share)
    return [{"hex": "#%02x%02x%02x" % tuple(int(c) for c in centres[i][::-1]), "share": round(float(share[i]), 2)}
            for i in order]


# ---------- product pack ----------
class Pack:
    MIN_INLIERS = 20  # tested: unrelated packs reached 11, real sightings 198+

    def __init__(self, path):
        self.sift = cv2.SIFT_create()
        pack = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if pack is None:
            sys.exit(f"cannot read pack image {path}")
        scale = 600 / max(pack.shape)
        self.pack = cv2.resize(pack, None, fx=scale, fy=scale) if scale < 1 else pack
        self.kp, self.des = self.sift.detectAndCompute(self.pack, None)
        self.match = cv2.BFMatcher()

    def __call__(self, img):
        h, w = img.shape[:2]
        kp, des = self.sift.detectAndCompute(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), None)
        if des is None or self.des is None or len(des) < 2:
            return {"found": False, "inliers": 0}
        good = [m for m, n in (p for p in self.match.knnMatch(self.des, des, k=2) if len(p) == 2)
                if m.distance < 0.75 * n.distance]
        if len(good) < self.MIN_INLIERS:
            return {"found": False, "inliers": len(good)}
        src = np.float32([self.kp[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst = np.float32([kp[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
        H, inl = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
        inliers = int(inl.sum()) if inl is not None else 0
        if H is None or inliers < self.MIN_INLIERS:
            return {"found": False, "inliers": inliers}
        ph, pw = self.pack.shape
        corners = cv2.perspectiveTransform(np.float32([[0, 0], [pw, 0], [pw, ph], [0, ph]]).reshape(-1, 1, 2), H)
        area = cv2.contourArea(corners) / (w * h)
        if not 0.002 < area < 1.2:  # a degenerate fit is not a sighting
            return {"found": False, "inliers": inliers}
        sp = src[inl.ravel() == 1].reshape(-1, 2)
        if np.prod(sp.max(0) - sp.min(0)) < 0.1 * pw * ph:  # only a small part of the pack matched (e.g. the logo): size unknown
            return {"found": True, "inliers": inliers, "partial": True, "size_pct": None, "box": None}
        xs, ys = corners[:, 0, 0] / w, corners[:, 0, 1] / h
        return {"found": True, "inliers": inliers, "size_pct": round(min(area, 1) * 100, 1),
                "box": [round(float(np.clip(v, 0, 1)), 3) for v in (xs.min(), ys.min(), xs.max(), ys.max())]}


# ---------- main ----------
def frames_of(folder):
    fj = folder / "frames.json"
    if fj.exists():
        info = json.loads(fj.read_text(encoding="utf-8"))
        return [(f["time_s"], f["file"]) for f in info["frames"]], info.get("cuts_s", [])
    files = sorted(p.name for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXT and not p.name.startswith("sheet"))
    return [(None, f) for f in files], []


def main(folder, pack_path, hindi):
    folder = Path(folder)
    frames, cuts = frames_of(folder)
    if not frames:
        sys.exit(f"no frames.json and no images in {folder}")
    engines, faces = ocr_engines(hindi), Faces()
    pack = Pack(pack_path) if pack_path else None
    out = []
    for t, name in frames:
        img = cv2.imread(str(folder / name))
        if img is None:
            print(f"skipped unreadable {name}"); continue
        h, w = img.shape[:2]
        lines = read_text(engines, img)
        for l in lines:
            l["contrast"] = contrast(img, l["box"])
        m = {"file": name, "time_s": t, "size": [w, h], "text": lines, "text_area_pct": text_area(lines),
             "safe_zone": safe_zone(lines, w, h), "faces": faces(img), "colours": colours(img)}
        if pack:
            m["pack"] = pack(img)
        out.append(m)
    first = lambda key: next((m["time_s"] for m in out if key(m)), None)
    summary = {"frames": len(out), "frames_with_text": sum(1 for m in out if m["text"]),
               "frames_with_faces": sum(1 for m in out if m["faces"]) if faces.yunet is not None else None,
               "max_text_area_pct": max(m["text_area_pct"] for m in out),
               "safe_zone_hits": sum(len(m["safe_zone"] or []) for m in out), "cuts_s": cuts,
               "face_detector": faces.kind, "readers": ["latin"] + (["devanagari"] if hindi else [])}
    if out[0]["time_s"] is not None:
        summary.update(first_text_s=first(lambda m: m["text"]),
                       first_face_s=first(lambda m: m["faces"]) if faces.yunet is not None else None)
        if pack:
            summary["first_pack_s"] = first(lambda m: m["pack"]["found"])
    if pack:
        summary["frames_with_pack"] = sum(1 for m in out if m["pack"]["found"])
        summary["pack_image"] = str(pack_path)
    (folder / "measures.json").write_text(json.dumps({"summary": summary, "frames": out}, ensure_ascii=False, indent=1),
                                          encoding="utf-8")
    print(f"measures.json: {len(out)} frames, text in {summary['frames_with_text']}, faces in "
          f"{summary['frames_with_faces']}" + (f", pack in {summary['frames_with_pack']}" if pack else ""))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder")
    ap.add_argument("--pack", help="product pack image (competitors.json product_image)")
    ap.add_argument("--hindi", action="store_true", help="also read Devanagari text")
    a = ap.parse_args()
    main(a.folder, a.pack, a.hindi)
