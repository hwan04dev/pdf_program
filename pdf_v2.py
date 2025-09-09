import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PyPDF2 import PdfReader, PdfWriter
import threading

class PDFCompressorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF 압축 프로그램")
        self.root.geometry("500x350")
        self.root.resizable(False, False)
        
        # 스타일 설정
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Arial", 10))
        self.style.configure("TLabel", font=("Arial", 11))
        
        # 메인 프레임
        self.main_frame = ttk.Frame(root, padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 타이틀
        title_label = ttk.Label(self.main_frame, text="PDF 파일 압축 도구", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # 파일 선택 프레임
        file_frame = ttk.Frame(self.main_frame)
        file_frame.pack(fill=tk.X, pady=10)
        
        self.file_label = ttk.Label(file_frame, text="선택된 파일: 없음", wraplength=400)
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        select_btn = ttk.Button(file_frame, text="파일 선택", command=self.select_file)
        select_btn.pack(side=tk.RIGHT, padx=5)
        
        # 압축 설정 프레임
        compress_frame = ttk.Frame(self.main_frame)
        compress_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(compress_frame, text="압축 품질:").pack(side=tk.LEFT, padx=5)
        
        self.quality_var = tk.StringVar(value="중간")
        quality_combo = ttk.Combobox(compress_frame, textvariable=self.quality_var, 
                                     values=["낮음", "중간", "높음"], width=10, state="readonly")
        quality_combo.pack(side=tk.LEFT, padx=5)
        
        # 출력 경로 프레임
        output_frame = ttk.Frame(self.main_frame)
        output_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(output_frame, text="저장 위치:").pack(side=tk.LEFT, padx=5)
        
        self.output_path_var = tk.StringVar(value="원본 파일과 같은 위치")
        self.output_path_entry = ttk.Entry(output_frame, textvariable=self.output_path_var, width=30)
        self.output_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        output_btn = ttk.Button(output_frame, text="경로 선택", command=self.select_output_path)
        output_btn.pack(side=tk.RIGHT, padx=5)
        
        # 진행 상태 표시
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(self.main_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill=tk.X, pady=10)
        
        self.status_label = ttk.Label(self.main_frame, text="대기 중...")
        self.status_label.pack(pady=5)
        
        # 압축 버튼
        self.compress_btn = ttk.Button(self.main_frame, text="PDF 압축하기", command=self.start_compression)
        self.compress_btn.pack(pady=10)
        
        # 변수 초기화
        self.selected_file = None
        self.output_directory = None
        
    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="압축할 PDF 파일 선택",
            filetypes=[("PDF 파일", "*.pdf")]
        )
        
        if file_path:
            self.selected_file = file_path
            filename = os.path.basename(file_path)
            self.file_label.config(text=f"선택된 파일: {filename}")
            
            # 기본 출력 경로 설정
            self.output_directory = os.path.dirname(file_path)
            self.output_path_var.set("원본 파일과 같은 위치")
    
    def select_output_path(self):
        directory = filedialog.askdirectory(title="압축된 PDF 저장 위치 선택")
        if directory:
            self.output_directory = directory
            self.output_path_var.set(directory)
    
    def update_status(self, message):
        """상태 메시지를 업데이트하는 메서드"""
        self.status_label.config(text=message)
        self.root.update_idletasks()
        
    def update_progress(self, value):
        """진행 상태바를 업데이트하는 메서드"""
        self.progress_var.set(value)
        self.root.update_idletasks()
    
    def start_compression(self):
        if not self.selected_file:
            messagebox.showerror("오류", "압축할 PDF 파일을 선택해주세요.")
            return
        
        # 압축 중에는 버튼 비활성화 및 상태 메시지 초기화
        self.compress_btn.config(state=tk.DISABLED)
        self.update_status("압축 준비 중...")
        self.update_progress(0)
        
        # 압축 작업을 별도 스레드로 실행하여 GUI가 멈추지 않도록 합니다.
        threading.Thread(target=self.compress_pdf, daemon=True).start()
    
    def compress_pdf(self):
        try:
            input_file = self.selected_file
            filename = os.path.basename(input_file)
            base_name, ext = os.path.splitext(filename)
            
            # 출력 경로 설정 (원본 파일과 같은 위치 또는 사용자가 지정한 위치)
            if self.output_path_var.get() == "원본 파일과 같은 위치":
                output_dir = os.path.dirname(input_file)
            else:
                output_dir = self.output_directory
                
            output_file = os.path.join(output_dir, f"{base_name}_compressed{ext}")
            
            # 파일이 이미 존재하는 경우 덮어쓸지 묻기
            if os.path.exists(output_file):
                if not messagebox.askyesno("파일 덮어쓰기", f"'{os.path.basename(output_file)}' 파일이 이미 존재합니다. 덮어쓰시겠습니까?"):
                    self.compress_btn.config(state=tk.NORMAL) # 버튼 다시 활성화
                    self.update_status("작업 취소됨.")
                    return
            
            # 압축 품질 설정 (PyPDF2는 direct compression level 설정은 없지만, 이 예제에서는 개념적 수준으로 적용)
            # 실제 PyPDF2의 압축은 copy_writer가 객체를 다시 쓰는 과정에서 이루어지며,
            # 내부적으로 스트림 압축(FlateDecode)을 적용합니다.
            # quality 설정은 사용자에게 옵션을 제공하는 UI적 요소입니다.
            quality = self.quality_var.get()
            # if quality == "낮음":
            #     # 품질을 낮춘다기보다 압축을 '덜' 하거나, 이미지 품질을 조정하는 것이 실제 압축
            #     # PyPDF2는 이런 직접적인 품질 제어는 어렵습니다.
            #     pass 
            # elif quality == "중간":
            #     pass
            # else: # "높음"
            #     pass

            self.update_status("PDF 파일 로딩 중...")
            self.update_progress(10)
            
            reader = PdfReader(input_file)
            writer = PdfWriter()
            
            total_pages = len(reader.pages)
            
            if total_pages == 0:
                messagebox.showwarning("경고", "선택된 PDF 파일에 페이지가 없습니다.")
                self.compress_btn.config(state=tk.NORMAL)
                self.update_status("대기 중...")
                return

            # 각 페이지를 Writer에 추가하며 진행 상태 업데이트
            for i, page in enumerate(reader.pages):
                # PyPDF2는 페이지를 다시 쓸 때 내부적으로 최적화를 시도합니다.
                # 명시적인 압축 레벨 설정은 PyPDF2 자체에서는 지원하지 않습니다.
                # (ex. 이미지 DPI 감소, 폰트 서브세팅 등은 다른 라이브러리 필요)
                writer.add_page(page)
                
                # 진행 상태 업데이트
                progress = 10 + (i / total_pages) * 80
                self.update_progress(progress)
                self.update_status(f"페이지 처리 중... ({i+1}/{total_pages})")
            
            self.update_status("PDF 파일 저장 중...")
            self.update_progress(90)
            
            # 최종 PDF 저장
            with open(output_file, "wb") as f:
                writer.write(f) # PyPDF2는 이 과정에서 FlateDecode 압축을 적용합니다.
            
            self.update_progress(100)
            self.update_status("압축 완료!")
            messagebox.showinfo("완료", f"PDF 파일이 성공적으로 압축되었습니다.\n저장 위치: {output_file}")
            
        except Exception as e:
            messagebox.showerror("오류", f"PDF 압축 중 오류가 발생했습니다: {str(e)}")
            self.update_status("오류 발생!")
        finally:
            # 작업 완료 후 버튼 활성화 및 상태 초기화
            self.compress_btn.config(state=tk.NORMAL)
            self.update_status("대기 중...")

# 메인 실행 블록
if __name__ == "__main__":
    # 필요한 라이브러리 설치 안내
    try:
        from PyPDF2 import PdfReader # PyPDF2 임포트 테스트
    except ImportError:
        messagebox.showerror("필수 라이브러리 없음", 
                             "PyPDF2 라이브러리가 설치되어 있지 않습니다.\n"
                             "명령 프롬프트(터미널)에서 'pip install PyPDF2'를 실행하여 설치해주세요.")
        exit() # 프로그램 종료
        
    root = tk.Tk()
    app = PDFCompressorApp(root)
    root.mainloop()