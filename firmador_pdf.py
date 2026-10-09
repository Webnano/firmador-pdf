import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import fitz  # PyMuPDF


# =========================================================
# TOOLTIPS
# =========================================================
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show, add="+")
        widget.bind("<Leave>", self.hide, add="+")

    def show(self, event=None):
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 15
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw, text=self.text, justify="left",
            background="#fffde7", foreground="#333333",
            relief="solid", borderwidth=1,
            font=("Segoe UI", 9), padx=6, pady=3
        )
        label.pack()

    def hide(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


# =========================================================
# APLICACIÓN
# =========================================================
class PDFSignerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Firmador de PDFs en Lote")
        self.root.geometry("880x700")
        self.root.minsize(860, 600)
        self.root.resizable(True, True)

        self.pdf_folder = tk.StringVar()
        self.sig_image = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.position = tk.StringVar(value="Inferior derecha")
        self.size_pct = tk.DoubleVar(value=20.0)
        self.opacity = tk.DoubleVar(value=100.0)
        self.page_mode = tk.StringVar(value="Todas")
        self.offset_x = tk.DoubleVar(value=0.0)
        self.offset_y = tk.DoubleVar(value=0.0)
        self.rotation = tk.DoubleVar(value=0.0)

        self.dark_mode = False
        self.preview_pdf_name = tk.StringVar(value="(sin fondo)")
        self.use_pdf_bg = tk.BooleanVar(value=True)
        self.preview_pdf_path = None
        self.selected_pdfs = None
        self._pdf_bg_cache = {}

        self.dragging = False
        self.cancel_requested = False
        self.processing = False
        self.log_lines = []

        self.build_menu()
        self.build_ui()
        self.setup_shortcuts()

        for var in (self.size_pct, self.opacity, self.position,
                    self.page_mode, self.offset_x, self.offset_y, self.rotation):
            var.trace_add("write", lambda *_: self.update_preview())
        self.use_pdf_bg.trace_add("write", lambda *_: self.update_preview())

        self.root.after(200, self.update_preview)
        self.root.after(300, self.apply_theme)

    # ---------- MENÚ ----------
    def build_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Seleccionar carpeta de PDFs...",
                              accelerator="Ctrl+O", command=self.select_pdf_folder)
        file_menu.add_command(label="Seleccionar imagen de firma...",
                              accelerator="Ctrl+Shift+O", command=self.select_signature)
        file_menu.add_command(label="Seleccionar carpeta de salida...",
                              accelerator="Ctrl+S", command=self.select_output_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Seleccionar archivos a firmar...",
                              accelerator="Ctrl+E", command=self.open_file_selection)
        file_menu.add_separator()
        file_menu.add_command(label="Guardar configuración...",
                              accelerator="Ctrl+G", command=self.save_config)
        file_menu.add_command(label="Cargar configuración...",
                              accelerator="Ctrl+L", command=self.load_config)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", accelerator="Ctrl+Q", command=self.root.quit)
        menubar.add_cascade(label="Archivo", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_checkbutton(label="Modo oscuro",
                                   accelerator="Ctrl+D",
                                   variable=tk.BooleanVar(value=False),
                                   command=self.toggle_dark_mode)
        view_menu.add_checkbutton(label="Usar PDF real como fondo",
                                   variable=self.use_pdf_bg)
        menubar.add_cascade(label="Ver", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Ver registro", accelerator="F2", command=self.show_log)
        help_menu.add_command(label="Acerca de", command=self.show_about)
        menubar.add_cascade(label="Ayuda", menu=help_menu)

        self.root.config(menu=menubar)

    # ---------- ATAJOS ----------
    def setup_shortcuts(self):
        self.root.bind("<Control-o>", lambda e: self.select_pdf_folder())
        self.root.bind("<Control-Shift-O>", lambda e: self.select_signature())
        self.root.bind("<Control-s>", lambda e: self.select_output_folder())
        self.root.bind("<Control-e>", lambda e: self.open_file_selection())
        self.root.bind("<Control-g>", lambda e: self.save_config())
        self.root.bind("<Control-l>", lambda e: self.load_config())
        self.root.bind("<Control-d>", lambda e: self.toggle_dark_mode())
        self.root.bind("<Control-q>", lambda e: self.root.quit())
        self.root.bind("<Control-Return>", lambda e: self.process_pdfs())
        self.root.bind("<F2>", lambda e: self.show_log())
        self.root.bind("<Escape>", lambda e: self.request_cancel())

    # ---------- INTERFAZ ----------
    def build_ui(self):
        main = ttk.Frame(self.root, padding=8)
        main.pack(fill="both", expand=True)
        self.main_frame = main

        # --- Rutas ---
        folder_frame = ttk.LabelFrame(main, text="📁 Rutas", padding=8)
        folder_frame.pack(fill="x", pady=2)

        ttk.Label(folder_frame, text="Carpeta con los PDFs:").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(folder_frame, textvariable=self.pdf_folder, width=60).grid(row=0, column=1, padx=5, pady=2)
        b1 = ttk.Button(folder_frame, text="Seleccionar", command=self.select_pdf_folder)
        b1.grid(row=0, column=2, pady=2)
        ToolTip(b1, "Carpeta que contiene los PDFs a firmar\nAtajo: Ctrl+O")

        ttk.Label(folder_frame, text="Imagen de la firma (PNG/JPG):").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(folder_frame, textvariable=self.sig_image, width=60).grid(row=1, column=1, padx=5, pady=2)
        b2 = ttk.Button(folder_frame, text="Seleccionar", command=self.select_signature)
        b2.grid(row=1, column=2, pady=2)
        ToolTip(b2, "Imagen de la firma. Se recomienda PNG con fondo transparente\nAtajo: Ctrl+Shift+O")

        ttk.Label(folder_frame, text="Carpeta de salida:").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Entry(folder_frame, textvariable=self.output_folder, width=60).grid(row=2, column=1, padx=5, pady=2)
        b3 = ttk.Button(folder_frame, text="Seleccionar", command=self.select_output_folder)
        b3.grid(row=2, column=2, pady=2)
        ToolTip(b3, "Carpeta donde se guardarán los PDFs firmados\nLos originales no se modifican\nAtajo: Ctrl+S")

        # --- Opciones ---
        opts_frame = ttk.LabelFrame(main, text="⚙️ Opciones de la firma", padding=8)
        opts_frame.pack(fill="x", pady=2)

        ttk.Label(opts_frame, text="Posición base:").grid(row=0, column=0, sticky="w", pady=2)
        self.cb_pos = ttk.Combobox(opts_frame, textvariable=self.position, width=22,
                     values=["Inferior derecha", "Inferior izquierda",
                             "Superior derecha", "Superior izquierda",
                             "Centro"],
                     state="readonly")
        self.cb_pos.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        ToolTip(self.cb_pos, "Punto de ancla desde el cual se aplican los ajustes finos")

        ttk.Label(opts_frame, text="Ancho (% de la página):").grid(row=0, column=2, sticky="w", padx=15, pady=2)
        self.sp_size = ttk.Spinbox(opts_frame, from_=5, to=80, textvariable=self.size_pct, width=6)
        self.sp_size.grid(row=0, column=3, sticky="w", pady=2)
        ToolTip(self.sp_size, "Ancho de la firma como % del ancho de la página")

        ttk.Label(opts_frame, text="Páginas a firmar:").grid(row=1, column=0, sticky="w", pady=2)
        self.cb_pages = ttk.Combobox(opts_frame, textvariable=self.page_mode, width=22,
                     values=["Todas", "Solo primera", "Solo última"],
                     state="readonly")
        self.cb_pages.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        ToolTip(self.cb_pages, "En qué páginas se insertará la firma")

        ttk.Label(opts_frame, text="Opacidad (%):").grid(row=1, column=2, sticky="w", padx=15, pady=2)
        self.sp_op = ttk.Spinbox(opts_frame, from_=10, to=100, textvariable=self.opacity, width=6)
        self.sp_op.grid(row=1, column=3, sticky="w", pady=2)
        ToolTip(self.sp_op, "Opacidad de la firma. 100% = totalmente opaca")

        ttk.Separator(opts_frame, orient="horizontal").grid(
            row=2, column=0, columnspan=4, sticky="ew", pady=4)

        ttk.Label(opts_frame, text="◀  Ajuste horizontal  ▶").grid(row=3, column=0, sticky="w", pady=2)
        s1 = ttk.Scale(opts_frame, from_=-50, to=50, variable=self.offset_x,
                  orient="horizontal", length=260)
        s1.grid(row=3, column=1, sticky="w", padx=5, pady=2)
        ToolTip(s1, "Desplazamiento horizontal respecto a la posición base")
        self.lbl_ox = ttk.Label(opts_frame, text="  +0.0 %", width=9,
                                foreground="#0055aa", font=("Arial", 9, "bold"))
        self.lbl_ox.grid(row=3, column=2, columnspan=2, sticky="w", pady=2)

        ttk.Label(opts_frame, text="▲  Ajuste vertical  ▼").grid(row=4, column=0, sticky="w", pady=2)
        s2 = ttk.Scale(opts_frame, from_=-50, to=50, variable=self.offset_y,
                  orient="horizontal", length=260)
        s2.grid(row=4, column=1, sticky="w", padx=5, pady=2)
        ToolTip(s2, "Desplazamiento vertical respecto a la posición base")
        self.lbl_oy = ttk.Label(opts_frame, text="  +0.0 %", width=9,
                                foreground="#0055aa", font=("Arial", 9, "bold"))
        self.lbl_oy.grid(row=4, column=2, columnspan=2, sticky="w", pady=2)

        ttk.Label(opts_frame, text="↻  Inclinación (°)").grid(row=5, column=0, sticky="w", pady=2)
        s3 = ttk.Scale(opts_frame, from_=-15, to=15, variable=self.rotation,
                  orient="horizontal", length=260)
        s3.grid(row=5, column=1, sticky="w", padx=5, pady=2)
        ToolTip(s3, "Ángulo de inclinación. Las firmas manuscritas rara vez son horizontales")
        self.lbl_rot = ttk.Label(opts_frame, text="  0.0°", width=9,
                                 foreground="#0055aa", font=("Arial", 9, "bold"))
        self.lbl_rot.grid(row=5, column=2, columnspan=2, sticky="w", pady=2)

        # --- Fila única con TODOS los botones de acción ---
        btn_frame = ttk.Frame(opts_frame)
        btn_frame.grid(row=6, column=0, columnspan=4, sticky="ew", pady=(8, 2))

        ttk.Button(btn_frame, text="↺ Restablecer",
                   command=self.reset_offsets).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="💾 Guardar",
                   command=self.save_config).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="📂 Cargar",
                   command=self.load_config).pack(side="left", padx=2)

        self.btn_sel = ttk.Button(btn_frame, text="☑ Elegir archivos",
                                   command=self.open_file_selection)
        self.btn_sel.pack(side="left", padx=2)
        ToolTip(self.btn_sel, "Elegir manualmente qué PDFs procesar\nAtajo: Ctrl+E")

        # Separador visual entre acciones y ejecución
        ttk.Separator(btn_frame, orient="vertical").pack(side="left", fill="y", padx=8)

        # --- Botón Procesar (destacado, al lado de Elegir archivos) ---
        self.btn_procesar = tk.Button(
            btn_frame, text="Procesar", command=self.process_pdfs,
            font=("Segoe UI", 11, "bold"),
            bg="#1E88E5", fg="white",
            activebackground="#1565C0", activeforeground="white",
            relief="flat", bd=0, padx=22, pady=4, cursor="hand2"
        )
        self.btn_procesar.pack(side="left", padx=2)
        self.btn_procesar.bind("<Enter>", lambda e: self._hover(self.btn_procesar, "#1565C0"))
        self.btn_procesar.bind("<Leave>", lambda e: self._hover(self.btn_procesar, "#1E88E5"))
        ToolTip(self.btn_procesar, "Procesa los PDFs según la configuración actual\nAtajo: Ctrl+Enter")

        # --- Botón Cancelar ---
        self.btn_cancelar = tk.Button(
            btn_frame, text="Cancelar", command=self.request_cancel,
            font=("Segoe UI", 10, "bold"),
            bg="#E53935", fg="white",
            activebackground="#C62828", activeforeground="white",
            relief="flat", bd=0, padx=16, pady=4, cursor="hand2",
            state="disabled", disabledforeground="#dddddd"
        )
        self.btn_cancelar.pack(side="left", padx=2)
        self.btn_cancelar.bind("<Enter>", lambda e: self._hover(self.btn_cancelar, "#C62828"))
        self.btn_cancelar.bind("<Leave>", lambda e: self._hover(self.btn_cancelar, "#E53935"))

        # --- Botón Ver registro ---
        self.btn_log = tk.Button(
            btn_frame, text="Registro", command=self.show_log,
            font=("Segoe UI", 10),
            bg="#757575", fg="white",
            activebackground="#616161", activeforeground="white",
            relief="flat", bd=0, padx=14, pady=4, cursor="hand2"
        )
        self.btn_log.pack(side="left", padx=2)
        self.btn_log.bind("<Enter>", lambda e: self._hover(self.btn_log, "#616161"))
        self.btn_log.bind("<Leave>", lambda e: self._hover(self.btn_log, "#757575"))
        ToolTip(self.btn_log, "Ver el detalle de la última ejecución\nAtajo: F2")

        # --- Vista previa ---
        preview_frame = ttk.LabelFrame(main, text="👁️ Vista previa", padding=5)
        preview_frame.pack(fill="both", expand=True, pady=2)

        toolbar = ttk.Frame(preview_frame)
        toolbar.pack(fill="x", pady=(0, 3))
        ttk.Label(toolbar, text="Fondo:").pack(side="left", padx=(2, 4))
        self.cb_bg = ttk.Combobox(toolbar, textvariable=self.preview_pdf_name,
                                   state="readonly", width=42)
        self.cb_bg.pack(side="left")
        self.cb_bg.bind("<<ComboboxSelected>>", self.on_bg_selected)
        ToolTip(self.cb_bg, "Elige un PDF para verlo como fondo del preview")

        ttk.Checkbutton(toolbar, text="PDF real",
                        variable=self.use_pdf_bg).pack(side="left", padx=8)

        ttk.Label(toolbar, text="💡 Arrastra la firma para moverla",
                  foreground="#777", font=("Arial", 8, "italic")).pack(side="right")

        self.preview_canvas = tk.Canvas(preview_frame, bg="white",
                                         highlightthickness=1, highlightbackground="#cccccc",
                                         cursor="hand2")
        self.preview_canvas.pack(fill="both", expand=True)
        self.preview_canvas.bind("<Configure>", lambda e: self.update_preview())
        self.preview_canvas.bind("<Button-1>", self.on_preview_press)
        self.preview_canvas.bind("<B1-Motion>", self.on_preview_drag)
        self.preview_canvas.bind("<ButtonRelease-1>", self.on_preview_release)

        # --- Estado / progreso (fila compacta al final) ---
        self.status = ttk.Label(main, text="Listo. Selecciona las carpetas y pulsa Procesar.",
                                foreground="#555")
        self.status.pack(pady=(6, 2))

        self.progress = ttk.Progressbar(main, mode="determinate")
        self.progress.pack(fill="x", pady=(0, 4))

    def _hover(self, btn, color):
        if str(btn["state"]) != "disabled":
            btn.config(bg=color)

    # ---------- MODO OSCURO ----------
    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def apply_theme(self):
        dark = self.dark_mode
        bg_root = "#2b2b2b" if dark else "#f0f0f0"
        bg_frame = "#2b2b2b" if dark else "#f0f0f0"
        fg = "#e0e0e0" if dark else "#000000"
        field_bg = "#3c3c3c" if dark else "#ffffff"
        field_fg = "#ffffff" if dark else "#000000"
        canvas_bg = "#1e1e1e" if dark else "white"
        label_accent = "#4fa8ff" if dark else "#0055aa"

        self.root.configure(bg=bg_root)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("TFrame", background=bg_frame)
        style.configure("TLabel", background=bg_frame, foreground=fg)
        style.configure("TLabelframe", background=bg_frame, foreground=fg,
                        bordercolor="#555555" if dark else "#cccccc")
        style.configure("TLabelframe.Label", background=bg_frame, foreground=fg)
        style.configure("TButton", background=field_bg, foreground=field_fg)
        style.map("TButton",
                  background=[("active", "#4a4a4a" if dark else "#e0e0e0")])
        style.configure("TEntry", fieldbackground=field_bg, foreground=field_fg,
                        insertcolor=field_fg)
        style.configure("TCombobox", fieldbackground=field_bg, foreground=field_fg,
                        background=field_bg, arrowcolor=field_fg)
        style.map("TCombobox",
                  fieldbackground=[("readonly", field_bg)],
                  foreground=[("readonly", field_fg)])
        style.configure("TSpinbox", fieldbackground=field_bg, foreground=field_fg,
                        background=field_bg)
        style.configure("TCheckbutton", background=bg_frame, foreground=fg)
        style.map("TCheckbutton", background=[("active", bg_frame)])
        style.configure("Horizontal.TScale", background=bg_frame)
        style.configure("TProgressbar", background="#1E88E5")

        self.preview_canvas.configure(bg=canvas_bg,
                                       highlightbackground="#555555" if dark else "#cccccc")

        self.lbl_ox.configure(foreground=label_accent)
        self.lbl_oy.configure(foreground=label_accent)
        self.lbl_rot.configure(foreground=label_accent)
        self.status.configure(foreground="#cccccc" if dark else "#555")

    # ---------- SELECCIÓN DE RUTAS ----------
    def select_pdf_folder(self):
        folder = filedialog.askdirectory(title="Carpeta con los PDFs originales")
        if folder:
            self.pdf_folder.set(folder)
            if not self.output_folder.get():
                self.output_folder.set(os.path.join(os.path.dirname(folder), "PDFs_firmados"))
            self.selected_pdfs = None
            self.reload_pdf_list()

    def select_signature(self):
        file = filedialog.askopenfilename(
            title="Selecciona la imagen de la firma",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp"), ("Todos", "*.*")]
        )
        if file:
            self.sig_image.set(file)
            self.update_preview()

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Carpeta donde guardar los PDFs firmados")
        if folder:
            self.output_folder.set(folder)

    def reset_offsets(self):
        self.offset_x.set(0.0)
        self.offset_y.set(0.0)
        self.rotation.set(0.0)

    # ---------- LISTA DE PDFs PARA PREVIEW ----------
    def reload_pdf_list(self):
        folder = self.pdf_folder.get()
        self._pdf_bg_cache.clear()

        if not folder or not os.path.isdir(folder):
            self.cb_bg["values"] = ["(sin fondo)"]
            self.preview_pdf_name.set("(sin fondo)")
            self.preview_pdf_path = None
            self.update_preview()
            return

        pdfs = sorted(f for f in os.listdir(folder) if f.lower().endswith(".pdf"))
        valores = ["(sin fondo)"] + pdfs
        self.cb_bg["values"] = valores

        if pdfs:
            self.preview_pdf_name.set(pdfs[0])
            self.preview_pdf_path = os.path.join(folder, pdfs[0])
        else:
            self.preview_pdf_name.set("(sin fondo)")
            self.preview_pdf_path = None
        self.update_preview()

    def on_bg_selected(self, event=None):
        folder = self.pdf_folder.get()
        name = self.preview_pdf_name.get()
        if name and name != "(sin fondo)" and folder:
            self.preview_pdf_path = os.path.join(folder, name)
        else:
            self.preview_pdf_path = None
        self.update_preview()

    def _get_pdf_first_page_image(self, pdf_path):
        if pdf_path in self._pdf_bg_cache:
            return self._pdf_bg_cache[pdf_path]
        doc = fitz.open(pdf_path)
        page = doc[0]
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        doc.close()
        self._pdf_bg_cache[pdf_path] = img
        return img

    # ---------- CONFIGURACIÓN ----------
    def save_config(self):
        data = {
            "position": self.position.get(),
            "size_pct": self.size_pct.get(),
            "opacity": self.opacity.get(),
            "page_mode": self.page_mode.get(),
            "offset_x": self.offset_x.get(),
            "offset_y": self.offset_y.get(),
            "rotation": self.rotation.get(),
            "dark_mode": self.dark_mode,
            "last_pdf_folder": self.pdf_folder.get(),
            "last_output_folder": self.output_folder.get(),
        }
        path = filedialog.asksaveasfilename(
            title="Guardar configuración",
            defaultextension=".json",
            filetypes=[("Archivo JSON", "*.json")],
            initialfile="firmador_config.json"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Configuración", f"Guardada en:\n{path}")
            self.log(f"💾 Configuración guardada en {path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar:\n{e}")

    def load_config(self):
        path = filedialog.askopenfilename(
            title="Cargar configuración",
            filetypes=[("Archivo JSON", "*.json"), ("Todos", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.position.set(data.get("position", "Inferior derecha"))
            self.size_pct.set(data.get("size_pct", 20.0))
            self.opacity.set(data.get("opacity", 100.0))
            self.page_mode.set(data.get("page_mode", "Todas"))
            self.offset_x.set(data.get("offset_x", 0.0))
            self.offset_y.set(data.get("offset_y", 0.0))
            self.rotation.set(data.get("rotation", 0.0))
            if data.get("dark_mode") and not self.dark_mode:
                self.toggle_dark_mode()
            elif not data.get("dark_mode") and self.dark_mode:
                self.toggle_dark_mode()
            if data.get("last_pdf_folder"):
                self.pdf_folder.set(data["last_pdf_folder"])
                self.reload_pdf_list()
            if data.get("last_output_folder"):
                self.output_folder.set(data["last_output_folder"])
            messagebox.showinfo("Configuración", "Configuración cargada correctamente.")
            self.log(f"📂 Configuración cargada desde {path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar:\n{e}")

    # ---------- SELECCIÓN INDIVIDUAL DE ARCHIVOS ----------
    def open_file_selection(self):
        folder = self.pdf_folder.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showwarning("Aviso", "Selecciona primero la carpeta con los PDFs.")
            return

        pdfs = sorted(f for f in os.listdir(folder) if f.lower().endswith(".pdf"))
        if not pdfs:
            messagebox.showinfo("Aviso", "No hay PDFs en la carpeta seleccionada.")
            return

        win = tk.Toplevel(self.root)
        win.title("Seleccionar archivos a firmar")
        win.geometry("520x560")
        win.transient(self.root)
        win.grab_set()

        self.root.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - 520) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - 560) // 2
        win.geometry(f"+{x}+{y}")

        header = ttk.Frame(win, padding=8)
        header.pack(fill="x")
        ttk.Label(header, text=f"{len(pdfs)} PDFs encontrados",
                  font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Label(header, text="Marca los que quieres procesar",
                  foreground="#777").pack(anchor="w")

        canvas_frame = ttk.Frame(win)
        canvas_frame.pack(fill="both", expand=True, padx=8)

        canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)

        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        vars_map = {}
        preseleccion = self.selected_pdfs if self.selected_pdfs is not None else set(pdfs)

        for name in pdfs:
            var = tk.BooleanVar(value=(name in preseleccion))
            vars_map[name] = var
            cb = ttk.Checkbutton(inner, text=name, variable=var)
            cb.pack(anchor="w", padx=4, pady=1)

        footer = ttk.Frame(win, padding=8)
        footer.pack(fill="x")

        def select_all():
            for v in vars_map.values():
                v.set(True)

        def deselect_all():
            for v in vars_map.values():
                v.set(False)

        def invert():
            for v in vars_map.values():
                v.set(not v.get())

        def aplicar():
            seleccionados = {n for n, v in vars_map.items() if v.get()}
            if len(seleccionados) == len(pdfs):
                self.selected_pdfs = None
                self.log(f"☑ Selección: todos los archivos ({len(pdfs)})")
            elif not seleccionados:
                messagebox.showwarning("Aviso", "No has seleccionado ningún archivo.")
                return
            else:
                self.selected_pdfs = seleccionados
                self.log(f"☑ Selección: {len(seleccionados)} de {len(pdfs)} archivos")
            self.status.config(text=f"Archivos seleccionados: "
                                     f"{len(seleccionados)} de {len(pdfs)}")
            canvas.unbind_all("<MouseWheel>")
            win.destroy()

        def cancelar():
            canvas.unbind_all("<MouseWheel>")
            win.destroy()

        ttk.Button(footer, text="Todos", command=select_all).pack(side="left", padx=2)
        ttk.Button(footer, text="Ninguno", command=deselect_all).pack(side="left", padx=2)
        ttk.Button(footer, text="Invertir", command=invert).pack(side="left", padx=2)
        ttk.Button(footer, text="Cancelar", command=cancelar).pack(side="right", padx=2)
        ttk.Button(footer, text="Aplicar", command=aplicar).pack(side="right", padx=2)

    # ---------- LOG ----------
    def log(self, msg):
        self.log_lines.append(msg)
        self.status.config(text=msg[:90])

    def show_log(self):
        win = tk.Toplevel(self.root)
        win.title("Registro de actividad")
        win.geometry("700x400")
        win.transient(self.root)

        frame = ttk.Frame(win, padding=8)
        frame.pack(fill="both", expand=True)

        txt = tk.Text(frame, wrap="word", font=("Consolas", 9))
        txt.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=txt.yview)
        scroll.pack(side="right", fill="y")
        txt.config(yscrollcommand=scroll.set)

        if self.log_lines:
            txt.insert("1.0", "\n".join(self.log_lines))
        else:
            txt.insert("1.0", "(Sin actividad todavía)")
        txt.config(state="disabled")
        txt.see("end")

        ttk.Button(win, text="Cerrar", command=win.destroy).pack(pady=6)

    def show_about(self):
        messagebox.showinfo(
            "Acerca de",
            "Firmador de PDFs en Lote v0.2\n\n"
            "Atajos:\n"
            "  Ctrl+O  Carpeta de PDFs\n"
            "  Ctrl+Shift+O  Imagen de firma\n"
            "  Ctrl+S  Carpeta de salida\n"
            "  Ctrl+E  Seleccionar archivos\n"
            "  Ctrl+G  Guardar config\n"
            "  Ctrl+L  Cargar config\n"
            "  Ctrl+D  Modo oscuro\n"
            "  Ctrl+Enter  Procesar\n"
            "  F2  Ver registro\n"
            "  Esc  Cancelar procesamiento\n"
            "  Ctrl+Q  Salir"
        )

    # ---------- GEOMETRÍA AUXILIAR ----------
    def get_page_rect(self):
        w = self.preview_canvas.winfo_width() or 760
        h = self.preview_canvas.winfo_height() or 200
        margin = 12
        return margin, margin, w - margin, h - margin

    def _get_rotated_image(self, img):
        angle = self.rotation.get()
        if abs(angle) < 0.1:
            return img
        return img.rotate(-angle, expand=True, resample=Image.BICUBIC)

    def get_signature_size(self, page_w, page_h):
        sig_path = self.sig_image.get()
        ratio = 0.4
        if sig_path and os.path.exists(sig_path):
            try:
                with Image.open(sig_path) as im:
                    im = self._get_rotated_image(im)
                    ratio = im.height / im.width
            except Exception:
                pass
        sig_w = page_w * (self.size_pct.get() / 100.0)
        sig_h = sig_w * ratio
        return sig_w, sig_h

    def compute_position(self, page_left, page_top, page_w, page_h, sig_w, sig_h):
        margin = 15
        pos = self.position.get()
        if pos == "Inferior derecha":
            bx = page_left + page_w - sig_w - margin
            by = page_top + page_h - sig_h - margin
        elif pos == "Inferior izquierda":
            bx = page_left + margin
            by = page_top + page_h - sig_h - margin
        elif pos == "Superior derecha":
            bx = page_left + page_w - sig_w - margin
            by = page_top + margin
        elif pos == "Superior izquierda":
            bx = page_left + margin
            by = page_top + margin
        else:
            bx = page_left + (page_w - sig_w) / 2
            by = page_top + (page_h - sig_h) / 2

        bx += page_w * (self.offset_x.get() / 100.0)
        by += page_h * (self.offset_y.get() / 100.0)
        return bx, by

    # ---------- VISTA PREVIA ----------
    def update_preview(self):
        self.preview_canvas.delete("all")
        left, top, right, bottom = self.get_page_rect()
        page_w = right - left
        page_h = bottom - top

        usar_pdf = self.use_pdf_bg.get() and self.preview_pdf_path and os.path.exists(self.preview_pdf_path)

        if usar_pdf:
            try:
                bg_img = self._get_pdf_first_page_image(self.preview_pdf_path)
                img_ratio = bg_img.width / bg_img.height
                rect_ratio = page_w / page_h
                if img_ratio > rect_ratio:
                    draw_w = page_w
                    draw_h = page_w / img_ratio
                else:
                    draw_h = page_h
                    draw_w = page_h * img_ratio
                x = left + (page_w - draw_w) / 2
                y = top + (page_h - draw_h) / 2
                self._bg_tk = ImageTk.PhotoImage(
                    bg_img.resize((max(1, int(draw_w)), max(1, int(draw_h))), Image.LANCZOS)
                )
                self.preview_canvas.create_image(x, y, anchor="nw", image=self._bg_tk)
                left, top, right, bottom = x, y, x + draw_w, y + draw_h
                page_w = draw_w
                page_h = draw_h
            except Exception:
                self._draw_simulated_page(left, top, right, bottom)
        else:
            self._draw_simulated_page(left, top, right, bottom)

        self.lbl_ox.config(text=f"  {self.offset_x.get():+.1f} %")
        self.lbl_oy.config(text=f"  {self.offset_y.get():+.1f} %")
        self.lbl_rot.config(text=f"  {self.rotation.get():+.1f}°")

        sig_path = self.sig_image.get()
        if not sig_path or not os.path.exists(sig_path):
            if not usar_pdf:
                self.preview_canvas.create_text((left + right) / 2, (top + bottom) / 2,
                                                 text="Selecciona una imagen de firma para verla aquí",
                                                 fill="#bbb")
            return

        try:
            img = Image.open(sig_path).convert("RGBA")
            img = self._get_rotated_image(img)
        except Exception:
            self.preview_canvas.create_text((left + right) / 2, (top + bottom) / 2,
                                             text="Error al abrir la imagen", fill="red")
            return

        sig_w, sig_h = self.get_signature_size(page_w, page_h)
        sig_h = max(1, sig_h)

        alpha = self.opacity.get() / 100.0
        if alpha < 1.0:
            img = img.copy()
            a = img.split()[3]
            a = a.point(lambda p: int(p * alpha))
            img.putalpha(a)

        img_resized = img.resize((max(1, int(sig_w)), max(1, int(sig_h))), Image.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(img_resized)

        x, y = self.compute_position(left, top, page_w, page_h, sig_w, sig_h)
        self.preview_canvas.create_image(x, y, anchor="nw", image=self.tk_img)

    def _draw_simulated_page(self, left, top, right, bottom):
        self.preview_canvas.create_rectangle(left, top, right, bottom,
                                              outline="#999", fill="#fafafa")
        self.preview_canvas.create_text((left + right) / 2, top + 14,
                                         text="(simulación de página)",
                                         fill="#bbb", font=("Arial", 9))

    # ---------- ARRASTRE ----------
    def on_preview_press(self, event):
        self.dragging = True
        self.drag_to(event.x, event.y)

    def on_preview_drag(self, event):
        if self.dragging:
            self.drag_to(event.x, event.y)

    def on_preview_release(self, event):
        self.dragging = False

    def drag_to(self, mx, my):
        if not self.sig_image.get():
            return
        left, top, right, bottom = self._get_effective_page_rect()
        page_w = right - left
        page_h = bottom - top

        sig_w, sig_h = self.get_signature_size(page_w, page_h)
        target_x = mx - sig_w / 2
        target_y = my - sig_h / 2

        old_ox, old_oy = self.offset_x.get(), self.offset_y.get()
        self.offset_x.set(0.0)
        self.offset_y.set(0.0)
        base_x, base_y = self.compute_position(left, top, page_w, page_h, sig_w, sig_h)
        self.offset_x.set(old_ox)
        self.offset_y.set(old_oy)

        dx_pct = ((target_x - base_x) / page_w) * 100.0
        dy_pct = ((target_y - base_y) / page_h) * 100.0
        dx_pct = max(-50.0, min(50.0, dx_pct))
        dy_pct = max(-50.0, min(50.0, dy_pct))

        self.offset_x.set(round(dx_pct, 1))
        self.offset_y.set(round(dy_pct, 1))

    def _get_effective_page_rect(self):
        left, top, right, bottom = self.get_page_rect()
        page_w = right - left
        page_h = bottom - top

        usar_pdf = self.use_pdf_bg.get() and self.preview_pdf_path and os.path.exists(self.preview_pdf_path)
        if usar_pdf:
            try:
                bg_img = self._get_pdf_first_page_image(self.preview_pdf_path)
                img_ratio = bg_img.width / bg_img.height
                rect_ratio = page_w / page_h
                if img_ratio > rect_ratio:
                    draw_w = page_w
                    draw_h = page_w / img_ratio
                else:
                    draw_h = page_h
                    draw_w = page_h * img_ratio
                x = left + (page_w - draw_w) / 2
                y = top + (page_h - draw_h) / 2
                return x, y, x + draw_w, y + draw_h
            except Exception:
                pass
        return left, top, right, bottom

    # ---------- CANCELAR ----------
    def request_cancel(self):
        if self.processing:
            self.cancel_requested = True
            self.log("⏹ Cancelación solicitada…")

    # ---------- PROCESAMIENTO ----------
    def process_pdfs(self):
        if self.processing:
            return

        pdf_dir = self.pdf_folder.get()
        sig_path = self.sig_image.get()
        out_dir = self.output_folder.get()

        if not pdf_dir or not os.path.isdir(pdf_dir):
            messagebox.showerror("Error", "Selecciona una carpeta válida con PDFs.")
            return
        if not sig_path or not os.path.isfile(sig_path):
            messagebox.showerror("Error", "Selecciona una imagen de firma válida.")
            return
        if not out_dir:
            messagebox.showerror("Error", "Selecciona una carpeta de salida.")
            return

        os.makedirs(out_dir, exist_ok=True)

        todos = sorted(f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf"))
        if self.selected_pdfs is None:
            pdfs = todos
        else:
            pdfs = [f for f in todos if f in self.selected_pdfs]

        if not pdfs:
            messagebox.showwarning("Aviso", "No hay PDFs que procesar con la selección actual.")
            return

        self.cancel_requested = False
        self.processing = True
        self.log_lines = []
        self.btn_procesar.config(state="disabled", bg="#999999")
        self.btn_cancelar.config(state="normal")
        self.progress["maximum"] = len(pdfs)
        self.progress["value"] = 0
        self.log(f"▶ Inicio: {len(pdfs)} PDFs a procesar "
                 f"(de {len(todos)} en carpeta)")

        ok, errores, saltados = 0, 0, 0
        errores_detalle = []
        cancelado = False

        for i, pdf_name in enumerate(pdfs, 1):
            if self.cancel_requested:
                cancelado = True
                self.log(f"⏹ Cancelado en {i-1}/{len(pdfs)}")
                break

            self.status.config(text=f"Procesando {i}/{len(pdfs)}: {pdf_name}")
            self.root.update_idletasks()

            src = os.path.join(pdf_dir, pdf_name)
            dst = os.path.join(out_dir, pdf_name)
            try:
                result = self.sign_pdf(src, dst, sig_path)
                if result == "ok":
                    ok += 1
                    self.log(f"✔ {pdf_name}")
                elif result == "skip_pass":
                    saltados += 1
                    self.log(f"🔒 {pdf_name} — protegido con contraseña, omitido")
            except Exception as e:
                errores += 1
                errores_detalle.append(f"{pdf_name}: {e}")
                self.log(f"✘ {pdf_name}: {e}")

            self.progress["value"] = i

        self.processing = False
        self.cancel_requested = False
        self.btn_procesar.config(state="normal", bg="#1E88E5")
        self.btn_cancelar.config(state="disabled")

        if cancelado:
            self.status.config(text=f"⏹ Cancelado. Firmados: {ok}, errores: {errores}, omitidos: {saltados}.")
        else:
            self.status.config(text=f"✅ Completado: {ok} firmados, {errores} errores, {saltados} omitidos.")

        msg = (f"Se procesaron {len(pdfs)} PDFs.\n\n"
               f"✔ Firmados correctamente: {ok}\n"
               f"✘ Errores: {errores}\n"
               f"⏭ Omitidos: {saltados}\n\n"
               f"Guardados en:\n{out_dir}")
        if errores_detalle:
            msg += "\n\nDetalle de errores:\n" + "\n".join(errores_detalle[:5])
        messagebox.showinfo("Proceso terminado", msg)
        self.log("⏹ Proceso finalizado")

    def sign_pdf(self, src_path, dst_path, sig_path):
        doc = fitz.open(src_path)

        if doc.needs_pass:
            doc.close()
            return "skip_pass"

        img = Image.open(sig_path).convert("RGBA")
        img = self._get_rotated_image(img)

        alpha = self.opacity.get() / 100.0
        if alpha < 1.0:
            a = img.split()[3]
            a = a.point(lambda p: int(p * alpha))
            img.putalpha(a)

        tmp_sig = os.path.join(os.path.dirname(dst_path), f".__firma_tmp_{os.getpid()}.png")
        img.save(tmp_sig, "PNG")

        try:
            total = len(doc)
            if self.page_mode.get() == "Solo primera":
                paginas = [0]
            elif self.page_mode.get() == "Solo última":
                paginas = [total - 1]
            else:
                paginas = list(range(total))

            ratio = img.height / img.width
            offx_pct = self.offset_x.get() / 100.0
            offy_pct = self.offset_y.get() / 100.0
            pos = self.position.get()
            margin = 20

            for pno in paginas:
                page = doc[pno]
                rect = page.rect
                pw, ph = rect.width, rect.height

                sig_w = pw * (self.size_pct.get() / 100.0)
                sig_h = sig_w * ratio

                if pos == "Inferior derecha":
                    x0 = pw - sig_w - margin
                    y0 = ph - sig_h - margin
                elif pos == "Inferior izquierda":
                    x0 = margin
                    y0 = ph - sig_h - margin
                elif pos == "Superior derecha":
                    x0 = pw - sig_w - margin
                    y0 = margin
                elif pos == "Superior izquierda":
                    x0 = margin
                    y0 = margin
                else:
                    x0 = (pw - sig_w) / 2
                    y0 = (ph - sig_h) / 2

                x0 += pw * offx_pct
                y0 += ph * offy_pct

                target = fitz.Rect(x0, y0, x0 + sig_w, y0 + sig_h)
                page.insert_image(target, filename=tmp_sig, overlay=True)

            doc.save(dst_path, garbage=4, deflate=True)
        finally:
            doc.close()
            if os.path.exists(tmp_sig):
                os.remove(tmp_sig)

        return "ok"


if __name__ == "__main__":
    root = tk.Tk()
    app = PDFSignerApp(root)
    root.mainloop()