#!/usr/bin/env python3
"""
RPM 공통수학1 PDF → 문제별 이미지 자동 추출 스크립트
사용법: python extract_questions.py RPM_공통수학1.pdf ./images/

필요 패키지:
  pip install pdf2image pillow
  (Windows) poppler 설치 필요: https://github.com/oschwartz10612/poppler-windows
"""

import sys
import os
import json
from pathlib import Path
from PIL import Image

try:
    from pdf2image import convert_from_path
except ImportError:
    print("❌ pdf2image 패키지가 없습니다. 아래 명령어로 설치하세요:")
    print("   pip install pdf2image pillow")
    sys.exit(1)

# ══════════════════════════════════════════
#  문제번호 → PDF 페이지 매핑 테이블
#  (RPM 공통수학1 기준, 실제 페이지 확인 후 수정)
# ══════════════════════════════════════════

# 각 페이지에서 문제가 몇 번부터 몇 번까지인지 정의
# 형식: { 페이지번호(0-based): (시작문항, 끝문항) }
PAGE_MAP = {
    # I. 다항식
    6:  (1, 22),      # 교과서 문제 정복하기
    7:  (23, 37),
    9:  (38, 53),     # 유형 익히기
    10: (54, 68),
    11: (69, 87),
    12: (88, 110),    # 시험에 꼭 나오는 문제
    # II. 항등식과 나머지정리
    20: (111, 123),
    21: (124, 138),
    22: (139, 152),
    23: (153, 172),
    24: (173, 195),
    # III. 인수분해
    32: (196, 222),
    33: (223, 243),
    34: (244, 263),
    35: (264, 279),
    # IV. 복소수
    44: (280, 308),
    45: (309, 338),
    46: (339, 375),
    # V. 이차방정식
    56: (376, 393),
    57: (394, 415),
    58: (416, 443),
    59: (444, 480),
    # VI. 이차방정식과 이차함수
    70: (481, 499),
    71: (500, 530),
    72: (531, 566),
}

# 한 페이지에 문제가 여러 개일 때 문제 위치 분할 설정
# 기본: 페이지를 세로로 N등분
SPLIT_MODE = "auto"   # "auto" | "manual"

def pdf_to_images(pdf_path: str, dpi: int = 200) -> list:
    """PDF를 페이지별 이미지로 변환"""
    print(f"📄 PDF 변환 중... (DPI: {dpi})")
    images = convert_from_path(pdf_path, dpi=dpi)
    print(f"   → 총 {len(images)} 페이지")
    return images

def crop_question(img: Image.Image, q_num: int, total_in_page: int, idx: int) -> Image.Image:
    """
    페이지 이미지에서 문제 영역 크롭
    - 좌우 여백 제거
    - 세로를 문제 수로 균등 분할
    """
    w, h = img.size
    # 여백 제거 (상하좌우 5%)
    margin_x = int(w * 0.03)
    margin_top = int(h * 0.04)
    margin_bot = int(h * 0.02)

    # 2열 레이아웃 처리 (RPM 교재는 좌우 2열)
    col = idx % 2          # 0: 왼쪽, 1: 오른쪽
    row = idx // 2
    rows_in_page = (total_in_page + 1) // 2

    col_w = (w - margin_x * 2) // 2
    row_h = (h - margin_top - margin_bot) // max(rows_in_page, 1)

    x1 = margin_x + col * col_w
    x2 = x1 + col_w - 4
    y1 = margin_top + row * row_h
    y2 = y1 + row_h - 4

    # 범위 클램핑
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)

    return img.crop((x1, y1, x2, y2))

def full_page_crop(img: Image.Image) -> Image.Image:
    """페이지 여백만 제거 (문제가 1개일 때)"""
    w, h = img.size
    mx = int(w * 0.03)
    my = int(h * 0.03)
    return img.crop((mx, my, w - mx, h - my))

def extract_all(pdf_path: str, out_dir: str, dpi: int = 200):
    """메인 추출 함수"""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    pages = pdf_to_images(pdf_path, dpi)
    saved = []
    skipped = []

    print(f"\n📁 출력 폴더: {out_path.absolute()}")
    print("─" * 50)

    for page_idx, (q_start, q_end) in PAGE_MAP.items():
        if page_idx >= len(pages):
            print(f"⚠ 페이지 {page_idx+1} 없음 (PDF가 {len(pages)}페이지)")
            continue

        page_img = pages[page_idx]
        q_count = q_end - q_start + 1

        print(f"📄 페이지 {page_idx+1:3d} → 문항 {q_start:04d}~{q_end:04d} ({q_count}개)")

        for i, q_num in enumerate(range(q_start, q_end + 1)):
            fname = f"q_{q_num:04d}.png"
            fpath = out_path / fname

            # 이미 존재하면 건너뜀
            if fpath.exists():
                skipped.append(q_num)
                continue

            # 크롭
            if q_count == 1:
                cropped = full_page_crop(page_img)
            else:
                cropped = crop_question(page_img, q_num, q_count, i)

            # 저장
            cropped.save(str(fpath), "PNG", optimize=True)
            saved.append(q_num)

    print("─" * 50)
    print(f"✅ 저장 완료: {len(saved)}개")
    print(f"⏭ 건너뜀 (기존): {len(skipped)}개")

    # 매핑되지 않은 문항 확인
    mapped = set()
    for q_start, q_end in PAGE_MAP.values():
        for n in range(q_start, q_end + 1):
            mapped.add(n)
    not_mapped = [n for n in range(1, 1185) if n not in mapped]
    if not_mapped:
        print(f"⚠ PAGE_MAP에 없는 문항 ({len(not_mapped)}개): {not_mapped[:10]}{'...' if len(not_mapped)>10 else ''}")

    # 결과 JSON 저장
    result = {
        "total_saved": len(saved),
        "total_skipped": len(skipped),
        "saved": saved,
        "not_mapped": not_mapped,
    }
    with open(out_path / "_extract_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n📝 결과 저장: {out_path / '_extract_result.json'}")

def verify_images(out_dir: str, total: int = 1184):
    """추출된 이미지 검증"""
    out_path = Path(out_dir)
    missing = []
    for n in range(1, total + 1):
        if not (out_path / f"q_{n:04d}.png").exists():
            missing.append(n)
    if missing:
        print(f"\n❌ 누락된 이미지 ({len(missing)}개): {missing[:20]}{'...' if len(missing)>20 else ''}")
    else:
        print(f"\n✅ 모든 {total}개 이미지가 존재합니다!")
    return missing

# ══════════════════════════════════════════
#  실행
# ══════════════════════════════════════════
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("사용법: python extract_questions.py <PDF경로> <출력폴더>")
        print("예시:   python extract_questions.py RPM_공통수학1.pdf ./images/")
        print()
        print("옵션:")
        print("  --dpi 300    해상도 설정 (기본값: 200)")
        print("  --verify     기존 이미지 검증만 실행")
        sys.exit(0)

    pdf_file = sys.argv[1]
    out_folder = sys.argv[2]
    dpi = 200

    # 옵션 파싱
    verify_only = "--verify" in sys.argv
    if "--dpi" in sys.argv:
        dpi_idx = sys.argv.index("--dpi")
        dpi = int(sys.argv[dpi_idx + 1])

    if verify_only:
        print(f"🔍 이미지 검증: {out_folder}")
        verify_images(out_folder)
    else:
        if not os.path.exists(pdf_file):
            print(f"❌ PDF 파일을 찾을 수 없습니다: {pdf_file}")
            sys.exit(1)
        print(f"🚀 RPM 공통수학1 문제 이미지 추출기")
        print(f"   PDF: {pdf_file}")
        print(f"   출력: {out_folder}")
        print(f"   DPI: {dpi}")
        print()
        extract_all(pdf_file, out_folder, dpi)
        print()
        verify_images(out_folder)
        print("\n🎉 완료! student.html의 IMG_BASE 경로를 확인하세요.")
