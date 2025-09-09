import streamlit as st
import subprocess
import shutil
import sys
import os
import tempfile
from io import BytesIO

# --- PDF 압축 핵심 기능 (Ghostscript 호출) ---
def compress_pdf(input_path: str, output_path: str, quality_level: str) -> None:
    """
    Ghostscript를 사용하여 PDF를 압축합니다.
    - quality_level: 'screen', 'ebook', 'printer', 'prepress' 중 하나
    오류 발생 시 예외를 발생시킵니다.
    """
    gs_command = find_ghostscript_executable()
    if not gs_command:
        raise FileNotFoundError(
            "Ghostscript를 찾을 수 없습니다. Ghostscript를 설치하고 PATH 환경 변수에 추가하세요."
        )

    command = [
        gs_command,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS=/{quality_level}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_path}",
        input_path,
    ]

    startupinfo = None
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    result = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        startupinfo=startupinfo,
    )
    if result.returncode != 0:
        err = result.stderr.decode("utf-8", errors="ignore")
        raise RuntimeError(f"PDF 압축 중 오류가 발생했습니다.\n{err}")


def find_ghostscript_executable() -> str | None:
    """
    시스템에서 Ghostscript 실행 파일을 찾습니다.
    (Windows: gswin64c.exe, gswin32c.exe / Linux/macOS: gs)
    """
    if sys.platform == "win32":
        for cmd in ["gswin64c", "gswin32c", "gs"]:
            path = shutil.which(cmd)
            if path:
                return path
    else:  # Linux, macOS
        path = shutil.which("gs")
        if path:
            return path
    return None


# --- Streamlit 앱 ---
st.set_page_config(page_title="PDF 압축기 (Streamlit)", page_icon="🗜️", layout="centered")
st.title("🗜️ PDF 압축 프로그램")
st.write("Ghostscript를 사용하여 PDF 파일 용량을 줄여줍니다.")

# Ghostscript 상태 표시
with st.expander("환경 점검", expanded=False):
    gs_path = find_ghostscript_executable()
    if gs_path:
        st.success(f"Ghostscript 감지: {gs_path}")
    else:
        st.error(
            "Ghostscript가 설치되어 있지 않거나 PATH에 등록되어 있지 않습니다.\n"
            "Windows: gswin64c.exe (또는 gswin32c.exe) 설치 후 PATH 추가\n"
            "macOS/Linux: 'gs' 설치 후 PATH에 등록"
        )

# 파일 업로더
uploaded = st.file_uploader("PDF 파일 업로드", type=["pdf"], accept_multiple_files=False)

# 품질 선택
qualities = {
    "낮음 (화면용)": "screen",
    "중간 (전자책)": "ebook",
    "높음 (인쇄용)": "printer",
    "최고 (출판용)": "prepress",
}
quality_label = st.radio("압축 품질 선택", list(qualities.keys()), index=1, horizontal=True)
quality_value = qualities[quality_label]

# 출력 파일 이름 제안
default_output_name = "compressed.pdf"
if uploaded is not None:
    base_name = os.path.splitext(os.path.basename(uploaded.name))[0]
    default_output_name = f"{base_name}_compressed.pdf"

out_name = st.text_input("출력 파일명", value=default_output_name)

compress_clicked = st.button("압축 시작", type="primary", use_container_width=True, disabled=(uploaded is None))

if compress_clicked:
    if uploaded is None:
        st.warning("먼저 PDF 파일을 업로드하세요.")
        st.stop()

    if not out_name.strip().lower().endswith(".pdf"):
        out_name = out_name.strip() + ".pdf"

    # 업로드 파일을 임시 경로로 저장
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.pdf")
        output_path = os.path.join(tmpdir, "output.pdf")

        with open(input_path, "wb") as f:
            f.write(uploaded.getbuffer())

        try:
            with st.spinner("압축 중입니다... 잠시만 기다려주세요."):
                compress_pdf(input_path, output_path, quality_value)

            # 결과 로드
            with open(output_path, "rb") as f:
                data = f.read()

            original_size_mb = len(uploaded.getbuffer()) / (1024 * 1024)
            compressed_size_mb = len(data) / (1024 * 1024)
            reduction = (
                ((original_size_mb - compressed_size_mb) / original_size_mb) * 100
                if original_size_mb > 0
                else 0.0
            )

            st.success("압축이 완료되었습니다!")
            col1, col2, col3 = st.columns(3)
            col1.metric("원본 크기 (MB)", f"{original_size_mb:.2f}")
            col2.metric("압축 후 크기 (MB)", f"{compressed_size_mb:.2f}")
            col3.metric("감소율", f"{reduction:.1f}%")

            st.download_button(
                label="압축된 PDF 다운로드",
                data=data,
                file_name=out_name,
                mime="application/pdf",
                use_container_width=True,
            )
        except FileNotFoundError as e:
            st.error(str(e))
        except RuntimeError as e:
            st.error(str(e))
        except Exception as e:
            st.exception(e)

st.markdown("---")
st.caption("이 앱은 Ghostscript를 호출하여 PDF를 재압축합니다. 환경에 따라 결과가 다를 수 있습니다.")