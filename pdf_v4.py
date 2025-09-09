import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import os
import sys
import shutil
from PIL import Image, ImageTk
from datetime import datetime

class PDFCompressorApp:
    """
    향상된 PDF 압축 프로그램
    - 다양한 압축 품질 옵션 제공
    - 배치 처리 지원
    - 진행 상황 표시
    - 자동 Ghostscript 감지 및 설치 안내
    """
    def __init__(self, master):
        self.master = master
        self.master.title("PDF 압축기 Pro")
        self.master.geometry("650x500")
        self.master.resizable(True, True)
        
        # 아이콘 설정 (선택사항)
        try:
            self.master.iconbitmap("pdf_icon.ico")
        except:
            pass

        self.input_files = []
        self.output_dir = ""
        self.ghostscript_path = self.find_ghostscript()
        self.compression_levels = {
            "최고 품질 (최소 압축)": "/prepress",
            "고품질 (인쇄용)": "/printer",
            "중간 품질 (전자책)": "/ebook",
            "저품질 (웹용)": "/screen"
        }
        self.current_compression = "/ebook"
        
        # UI 초기화
        self.setup_ui()
        
        # Ghostscript 설치 확인
        self.check_ghostscript_installed()

    def setup_ui(self):
        """UI 컴포넌트 초기화"""
        # 메인 프레임
        main_frame = ttk.Frame(self.master, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 헤더
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(header_frame, text="PDF 압축기 Pro", font=('Helvetica', 16, 'bold')).pack(side=tk.LEFT)
        
        # 설정 프레임
        settings_frame = ttk.LabelFrame(main_frame, text="압축 설정", padding=10)
        settings_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 압축 품질 선택
        ttk.Label(settings_frame, text="압축 품질:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.compression_var = tk.StringVar(value="중간 품질 (전자책)")
        compression_menu = ttk.OptionMenu(settings_frame, self.compression_var, 
                                        "중간 품질 (전자책)", *self.compression_levels.keys())
        compression_menu.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 출력 폴더 선택
        ttk.Button(settings_frame, text="출력 폴더 선택", 
                  command=self.select_output_dir).grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.output_dir_var = tk.StringVar(value="원본 파일과 같은 폴더에 저장")
        ttk.Label(settings_frame, textvariable=self.output_dir_var, 
                 wraplength=400).grid(row=1, column=1, columnspan=2, sticky=tk.W, padx=5)
        
        # 파일 목록 프레임
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # 파일 목록 헤더
        ttk.Label(list_frame, text="선택된 파일 목록:").pack(anchor=tk.W)
        
        # 스크롤바가 있는 파일 목록
        self.file_listbox = tk.Listbox(list_frame, height=8, selectmode=tk.EXTENDED)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(button_frame, text="파일 추가", command=self.add_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="폴더 추가", command=self.add_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="선택 제거", command=self.remove_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="모두 지우기", command=self.clear_list).pack(side=tk.LEFT, padx=2)
        
        # 진행 상황
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill=tk.X, pady=(10, 5))
        
        self.status_var = tk.StringVar(value="준비됨")
        ttk.Label(main_frame, textvariable=self.status_var, style="Status.TLabel").pack(fill=tk.X)
        
        # 압축 버튼
        self.compress_btn = ttk.Button(main_frame, text="압축 시작", 
                                     command=self.start_compression,
                                     style="Accent.TButton")
        self.compress_btn.pack(fill=tk.X, pady=(10, 0))
        
        # 스타일 설정
        self.setup_styles()
    
    def setup_styles(self):
        """UI 스타일 설정"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 버튼 스타일
        style.configure('TButton', padding=6)
        style.map('TButton',
                 foreground=[('active', 'white')],
                 background=[('active', '#005a9e')])
        
        # 액센트 버튼 (주요 작업용)
        style.configure('Accent.TButton',
                      font=('Helvetica', 10, 'bold'),
                      padding=8,
                      background='#0078D7',
                      foreground='white')
        style.map('Accent.TButton',
                background=[('active', '#005a9e')])
        
        # 상태 레이블 스타일
        style.configure('Status.TLabel',
                      font=('Helvetica', 9),
                      foreground='gray')
    
    def find_ghostscript(self):
        """시스템에서 Ghostscript 실행 파일 찾기"""
        if sys.platform.startswith('win'):
            for cmd in ('gswin64c', 'gswin32c', 'gs'):
                path = shutil.which(cmd)
                if path:
                    return path
        else:
            path = shutil.which('gs')
            if path:
                return path
        return None
    
    def check_ghostscript_installed(self):
        """Ghostscript 설치 여부 확인"""
        if not self.ghostscript_path:
            self.show_error(
                "Ghostscript 미설치",
                "PDF 압축을 위해서는 Ghostscript가 필요합니다.\n\n"
                "Windows: ghostscript.com에서 설치\n"
                "macOS: 'brew install ghostscript' 실행\n"
                "Linux: 'sudo apt-get install ghostscript' 실행"
            )
            self.compress_btn.config(state=tk.DISABLED)
            self.status_var.set("오류: Ghostscript를 찾을 수 없음")
        else:
            self.status_var.set(f"Ghostscript 감지됨: {os.path.basename(self.ghostscript_path)}")
    
    def add_files(self):
        """파일 추가 대화상자 열기"""
        files = filedialog.askopenfilenames(
            title="PDF 파일 선택",
            filetypes=(
                ("PDF 파일", "*.pdf"),
                ("모든 파일", "*.*")
            )
        )
        
        if files:
            self.add_to_list(files)
    
    def add_folder(self):
        """폴더에서 PDF 파일 추가"""
        folder = filedialog.askdirectory(title="PDF 파일이 있는 폴더 선택")
        if folder:
            pdf_files = []
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        pdf_files.append(os.path.join(root, file))
            
            if pdf_files:
                self.add_to_list(pdf_files)
            else:
                self.show_warning("PDF 파일 없음", "선택한 폴더에서 PDF 파일을 찾을 수 없습니다.")
    
    def add_to_list(self, files):
        """파일 목록에 추가"""
        added = 0
        for file in files:
            if file not in self.input_files:
                self.input_files.append(file)
                self.file_listbox.insert(tk.END, os.path.basename(file))
                added += 1
        
        if added > 0:
            self.status_var.set(f"{added}개의 파일이 추가되었습니다. 총 {len(self.input_files)}개 파일")
            self.compress_btn.config(state=tk.NORMAL if self.ghostscript_path else tk.DISABLED)
    
    def remove_selected(self):
        """선택된 파일 제거"""
        selection = self.file_listbox.curselection()
        if not selection:
            return
            
        # 역순으로 제거 (인덱스가 바뀌지 않도록)
        for i in reversed(selection):
            self.input_files.pop(i)
            self.file_listbox.delete(i)
        
        self.status_var.set(f"{len(selection)}개 파일 제거됨. 남은 파일: {len(self.input_files)}개")
        
        if not self.input_files:
            self.compress_btn.config(state=tk.DISABLED)
    
    def clear_list(self):
        """모든 파일 제거"""
        if not self.input_files:
            return
            
        if messagebox.askyesno("확인", "모든 파일을 목록에서 제거하시겠습니까?"):
            self.input_files.clear()
            self.file_listbox.delete(0, tk.END)
            self.status_var.set("모든 파일이 제거되었습니다.")
            self.compress_btn.config(state=tk.DISABLED)
    
    def select_output_dir(self):
        """출력 폴더 선택"""
        folder = filedialog.askdirectory(title="압축된 PDF 저장 폴더 선택")
        if folder:
            self.output_dir = folder
            self.output_dir_var.set(folder)
    
    def start_compression(self):
        """압축 프로세스 시작"""
        if not self.input_files:
            self.show_warning("파일 없음", "압축할 PDF 파일을 추가하세요.")
            return
        
        # 압축 품질 설정
        self.current_compression = self.compression_levels.get(
            self.compression_var.get(), 
            "/ebook"  # 기본값
        )
        
        # 출력 폴더 설정
        output_dir = self.output_dir if self.output_dir else None
        
        # 압축 시작
        self.compress_btn.config(state=tk.DISABLED, text="압축 중...")
        self.master.update()
        
        try:
            total_files = len(self.input_files)
            success_count = 0
            
            for i, input_file in enumerate(self.input_files, 1):
                self.status_var.set(f"처리 중 ({i}/{total_files}): {os.path.basename(input_file)}")
                self.progress_var.set((i-1) / total_files * 100)
                self.master.update()
                
                try:
                    if self.compress_pdf(input_file, output_dir):
                        success_count += 1
                except Exception as e:
                    self.show_error("압축 오류", f"{os.path.basename(input_file)} 처리 중 오류: {str(e)}")
            
            # 완료 메시지
            self.progress_var.set(100)
            self.status_var.set(f"완료! {success_count}/{total_files}개 파일 압축 성공")
            
            if success_count > 0 and output_dir:
                if messagebox.askyesno("완료", f"{success_count}개 파일 압축 완료!\n\n압축된 파일이 저장된 폴더를 열까요?"):
                    self.open_folder(output_dir if output_dir else os.path.dirname(self.input_files[0]))
        
        except Exception as e:
            self.show_error("알 수 없는 오류", f"압축 중 오류가 발생했습니다: {str(e)}")
        
        finally:
            self.compress_btn.config(state=tk.NORMAL, text="압축 시작")
    
    def compress_pdf(self, input_file, output_dir=None):
        """단일 PDF 파일 압축"""
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {input_file}")
        
        # 출력 경로 설정
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(input_file))[0]}_compressed.pdf")
        else:
            dirname, filename = os.path.split(input_file)
            output_file = os.path.join(dirname, f"{os.path.splitext(filename)[0]}_compressed.pdf")
        
        # 중복 파일 확인
        if os.path.exists(output_file):
            if not messagebox.askyesno(
                "파일 덮어쓰기",
                f"'{os.path.basename(output_file)}' 파일이 이미 존재합니다.\n덮어쓰시겠습니까?"
            ):
                return False
        
        # Ghostscript 명령어 구성
        command = [
            self.ghostscript_path,
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            f"-dPDFSETTINGS={self.current_compression}",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            f"-sOutputFile={output_file}",
            input_file
        ]
        
        # 압축 실행
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Ghostscript 오류: {result.stderr}")
        
        # 원본과 동일한 파일이 생성되었는지 확인
        if not os.path.exists(output_file):
            raise RuntimeError("출력 파일이 생성되지 않았습니다.")
        
        return True
    
    def open_folder(self, folder_path):
        """파일 탐색기에서 폴더 열기"""
        if sys.platform == 'win32':
            os.startfile(folder_path)
        elif sys.platform == 'darwin':  # macOS
            subprocess.Popen(['open', folder_path])
        else:  # Linux
            subprocess.Popen(['xdg-open', folder_path])
    
    def show_error(self, title, message):
        """오류 메시지 표시"""
        messagebox.showerror(title, message)
        self.status_var.set(f"오류: {title}")
    
    def show_warning(self, title, message):
        """경고 메시지 표시"""
        messagebox.showwarning(title, message)
        self.status_var.set(f"경고: {title}")


def main():
    # High DPI 디스플레이 대응
    if sys.platform == 'win32':
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    
    # 애플리케이션 실행
    root = tk.Tk()
    app = PDFCompressorApp(root)
    
    # 창을 화면 중앙에 배치
    window_width = 650
    window_height = 500
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    root.geometry(f'{window_width}x{window_height}+{x}+{y}')
    
    # 실행
    root.mainloop()


if __name__ == "__main__":
    main()
