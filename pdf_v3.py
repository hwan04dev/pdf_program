import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import os
import sys
import shutil

class PDFCompressorApp:
    """
    tkinter를 사용하여 PDF 압축을 위한 GUI 애플리케이션 클래스
    """
    def __init__(self, master):
        self.master = master
        self.master.title("PDF 압축 프로그램")
        self.master.geometry("550x300")
        self.master.resizable(False, False)

        self.input_file_path = ""
        self.ghostscript_path = self.find_ghostscript()

        # 스타일 설정
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", padding=6, relief="flat", background="#0078D7", foreground="white")
        style.map("TButton", background=[('active', '#005a9e')])
        style.configure("TLabel", padding=5, font=('Helvetica', 10))
        style.configure("Status.TLabel", font=('Helvetica', 9), foreground="gray")
        style.configure("Header.TLabel", font=('Helvetica', 12, 'bold'))

        # 메인 프레임
        main_frame = ttk.Frame(master, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- 위젯 생성 ---
        header_label = ttk.Label(main_frame, text="PDF 압축기", style="Header.TLabel")
        header_label.pack(pady=(0, 15))
        
        # 파일 선택 프레임
        file_frame = ttk.Frame(main_frame)
        file_frame.pack(fill=tk.X, pady=5)

        self.file_label = ttk.Label(file_frame, text="선택된 파일이 없습니다.", wraplength=400)
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        select_button = ttk.Button(file_frame, text="PDF 파일 선택", command=self.select_file)
        select_button.pack(side=tk.RIGHT)
        
        # 압축 버튼
        self.compress_button = ttk.Button(main_frame, text="압축 시작", command=self.compress_pdf, state=tk.DISABLED)
        self.compress_button.pack(pady=20, fill=tk.X)
        
        # 상태 표시줄
        self.status_label = ttk.Label(main_frame, text="압축할 PDF 파일을 선택하세요.", style="Status.TLabel")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        # Ghostscript 설치 확인
        self.check_ghostscript_installed()

    def find_ghostscript(self):
        """
        시스템 경로에서 Ghostscript 실행 파일을 찾습니다.
        Windows와 Unix 계열 시스템을 모두 지원합니다.
        """
        if sys.platform.startswith('win'):
            # Windows에서는 gswin64c.exe 또는 gswin32c.exe를 찾습니다.
            for cmd in ('gswin64c', 'gswin32c', 'gs'):
                path = shutil.which(cmd)
                if path:
                    return path
        else:
            # Linux, macOS 등에서는 'gs'를 찾습니다.
            path = shutil.which('gs')
            if path:
                return path
        return None

    def check_ghostscript_installed(self):
        """
        Ghostscript가 설치되어 있는지 확인하고, 없으면 사용자에게 알립니다.
        """
        if not self.ghostscript_path:
            messagebox.showerror(
                "오류: Ghostscript 미설치",
                "PDF 압축을 위해서는 Ghostscript가 필요합니다.\n\n"
                "ghostscript.com에서 다운로드하여 설치한 후 프로그램을 다시 시작해주세요."
            )
            self.compress_button.config(state=tk.DISABLED)
            self.status_label.config(text="Ghostscript를 설치해야 합니다.")
        else:
            self.status_label.config(text=f"Ghostscript 감지됨: {os.path.basename(self.ghostscript_path)}")

    def select_file(self):
        """
        파일 대화상자를 열어 PDF 파일을 선택하게 합니다.
        """
        file_path = filedialog.askopenfilename(
            title="PDF 파일 선택",
            filetypes=(("PDF Files", "*.pdf"), ("All files", "*.*"))
        )
        if file_path:
            self.input_file_path = file_path
            self.file_label.config(text=os.path.basename(file_path))
            # Ghostscript가 설치된 경우에만 압축 버튼 활성화
            if self.ghostscript_path:
                self.compress_button.config(state=tk.NORMAL)
                self.status_label.config(text="압축할 준비가 되었습니다.")

    def compress_pdf(self):
        """
        선택된 PDF 파일을 Ghostscript를 사용하여 압축합니다.
        """
        if not self.input_file_path:
            messagebox.showwarning("파일 없음", "먼저 압축할 PDF 파일을 선택해주세요.")
            return

        # 저장될 파일 경로 설정 (예: original_compressed.pdf)
        path, ext = os.path.splitext(self.input_file_path)
        output_file_path = f"{path}_compressed.pdf"

        # 파일 덮어쓰기 방지
        if os.path.exists(output_file_path):
             if not messagebox.askyesno("파일 덮어쓰기", f"'{os.path.basename(output_file_path)}' 파일이 이미 존재합니다.\n덮어쓰시겠습니까?"):
                 self.status_label.config(text="압축이 취소되었습니다.")
                 return

        self.status_label.config(text="압축 중... 잠시만 기다려주세요.")
        self.master.update_idletasks()  # UI 업데이트 강제

        try:
            # Ghostscript 명령어 실행
            # -dPDFSETTINGS=/ebook: 중간 품질 및 크기로 압축 (옵션: /screen, /printer, /prepress)
            command = [
                self.ghostscript_path,
                "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.4",
                "-dPDFSETTINGS=/ebook",
                "-dNOPAUSE",
                "-dQUIET",
                "-dBATCH",
                f"-sOutputFile={output_file_path}",
                self.input_file_path
            ]
            
            # subprocess.run을 사용하여 Ghostscript 실행
            result = subprocess.run(command, check=True, capture_output=True, text=True)

            original_size = os.path.getsize(self.input_file_path) / (1024 * 1024)
            compressed_size = os.path.getsize(output_file_path) / (1024 * 1024)

            messagebox.showinfo(
                "압축 완료",
                f"PDF 압축이 성공적으로 완료되었습니다.\n\n"
                f"원본 크기: {original_size:.2f} MB\n"
                f"압축된 크기: {compressed_size:.2f} MB\n"
                f"저장 위치: {output_file_path}"
            )
            self.status_label.config(text="압축 완료!")

        except FileNotFoundError:
            messagebox.showerror("오류", f"Ghostscript 실행 파일을 찾을 수 없습니다: {self.ghostscript_path}")
            self.status_label.config(text="오류: Ghostscript를 찾을 수 없음")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("압축 오류", f"PDF 압축 중 오류가 발생했습니다.\n\n오류: {e.stderr}")
            self.status_label.config(text="오류: 압축 실패")
        except Exception as e:
            messagebox.showerror("알 수 없는 오류", f"알 수 없는 오류가 발생했습니다: {e}")
            self.status_label.config(text="오류 발생")


if __name__ == "__main__":
    root = tk.Tk()
    app = PDFCompressorApp(root)
    root.mainloop()