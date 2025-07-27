import sys
import os
import uuid
import json
import base64
from datetime import datetime, timedelta
from html import escape

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QComboBox, QPushButton, QTextEdit, QAction, QToolBar,
    QFileDialog, QMessageBox, QLabel, QDialog, QFormLayout, QSpinBox
)
from PyQt5.QtGui import QFont, QImage, QTextDocument, QTextCursor, QPixmap
from PyQt5.QtCore import Qt, QUrl, QMimeData, QBuffer, QIODevice

# Define the base directory for news files
NEWS_BASE_DIR = "News"

class ImageResizeDialog(QDialog):
    """Dialog to get new dimensions for an image."""
    def __init__(self, current_width, current_height, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Resize Image")
        self.setModal(True)

        self.layout = QFormLayout(self)

        self.width_input = QSpinBox()
        self.width_input.setRange(1, 4000)
        self.width_input.setValue(current_width)
        self.layout.addRow("Width:", self.width_input)

        self.height_input = QSpinBox()
        self.height_input.setRange(1, 4000)
        self.height_input.setValue(current_height)
        self.layout.addRow("Height:", self.height_input)

        self.ok_button = QPushButton("Insert")
        self.ok_button.clicked.connect(self.accept)
        self.layout.addRow(self.ok_button)

    def get_dimensions(self):
        return self.width_input.value(), self.height_input.value()

class AdvancedNewsEditorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("News Editor - Classic News")
        self.setGeometry(100, 100, 1000, 800)

        self.categories = [
            "Politics", "Science", "Health", "Sports", "India", "World",
            "Business", "Tech", "Travel", "Art"
        ]

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Headline and Category ---
        form_layout = QHBoxLayout()
        main_layout.addLayout(form_layout)

        form_layout.addWidget(QLabel("Headline:"))
        self.headline_input = QLineEdit()
        self.headline_input.setPlaceholderText("Enter news headline")
        form_layout.addWidget(self.headline_input)

        form_layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(self.categories)
        form_layout.addWidget(self.category_combo)

        # --- Text Editor (Moved to initialize before toolbar connections) ---
        self.text_editor = QTextEdit()
        self.text_editor.setAcceptRichText(True)
        self.text_editor.setPlaceholderText("Start writing your news article here...")
        main_layout.addWidget(self.text_editor)

        # Enable drag and drop for the text editor
        self.text_editor.setAcceptDrops(True)
        # These need to be assigned directly to the instance, not the class
        self.text_editor.dragEnterEvent = self.dragEnterEvent
        self.text_editor.dropEvent = self.dropEvent

        # --- Toolbar ---
        toolbar = QToolBar("Editor Toolbar")
        self.addToolBar(toolbar)

        # Bold
        bold_action = QAction("Bold", self)
        bold_action.setShortcut("Ctrl+B")
        bold_action.triggered.connect(lambda: self.text_editor.setFontWeight(
            QFont.Bold if self.text_editor.fontWeight() != QFont.Bold else QFont.Normal
        ))
        toolbar.addAction(bold_action)

        # Italic
        italic_action = QAction("Italic", self)
        italic_action.setShortcut("Ctrl+I")
        italic_action.triggered.connect(lambda: self.text_editor.setFontItalic(
            not self.text_editor.fontItalic()
        ))
        toolbar.addAction(italic_action)

        # Underline
        underline_action = QAction("Underline", self)
        underline_action.setShortcut("Ctrl+U")
        underline_action.triggered.connect(lambda: self.text_editor.setFontUnderline(
            not self.text_editor.fontUnderline()
        ))
        toolbar.addAction(underline_action)

        toolbar.addSeparator()

        # Font Family
        self.font_combo = QComboBox(self)
        self.font_combo.addItems(QFont().families())
        self.font_combo.setCurrentText("Arial") # Set a default
        # Connect to text_editor AFTER it's initialized
        self.font_combo.currentTextChanged.connect(self.text_editor.setFontFamily)
        toolbar.addWidget(self.font_combo)

        # Font Size
        self.size_combo = QComboBox(self)
        self.size_combo.addItems([str(s) for s in range(8, 73, 2)])
        self.size_combo.setCurrentText("12") # Set a default
        # Connect to text_editor AFTER it's initialized
        self.size_combo.currentTextChanged.connect(
            lambda s: self.text_editor.setFontPointSize(float(s))
        )
        toolbar.addWidget(self.size_combo)

        toolbar.addSeparator()

        # Align Left
        align_left_action = QAction("Align Left", self)
        align_left_action.triggered.connect(lambda: self.text_editor.setAlignment(Qt.AlignLeft))
        toolbar.addAction(align_left_action)

        # Align Center
        align_center_action = QAction("Align Center", self)
        align_center_action.triggered.connect(lambda: self.text_editor.setAlignment(Qt.AlignCenter))
        toolbar.addAction(align_center_action)

        # Align Right
        align_right_action = QAction("Align Right", self)
        align_right_action.triggered.connect(lambda: self.text_editor.setAlignment(Qt.AlignRight))
        toolbar.addAction(align_right_action)

        # Justify
        align_justify_action = QAction("Justify", self)
        align_justify_action.triggered.connect(lambda: self.text_editor.setAlignment(Qt.AlignJustify))
        toolbar.addAction(align_justify_action)

        toolbar.addSeparator()

        # Insert Image Button
        insert_image_action = QAction("Insert Image", self)
        insert_image_action.triggered.connect(self.insert_image_from_file)
        toolbar.addAction(insert_image_action)


        # --- Export Button ---
        export_button = QPushButton("Export News")
        export_button.clicked.connect(self.export_news)
        main_layout.addWidget(export_button)

    def insert_image_into_editor(self, image_path=None, image_data=None):
        """
        Inserts an image into the QTextEdit, optionally resizing it.
        Image can be from a file path or raw QImage data.
        """
        original_image = QImage()
        if image_path:
            original_image.load(image_path)
        elif image_data:
            original_image = image_data

        if original_image.isNull():
            QMessageBox.warning(self, "Image Error", "Could not load image.")
            return

        # Show resize dialog
        dialog = ImageResizeDialog(original_image.width(), original_image.height(), self)
        if dialog.exec_() == QDialog.Accepted:
            new_width, new_height = dialog.get_dimensions()

            # Resize the image
            resized_image = original_image.scaled(new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            # Convert QImage to QPixmap, then to Base64
            buffer = QBuffer()
            buffer.open(QIODevice.WriteOnly)
            resized_image.save(buffer, "PNG") # Save as PNG
            base64_data = base64.b64encode(buffer.data().data()).decode("utf-8")
            buffer.close()

            # Insert image as HTML
            image_html = f'<img src="data:image/png;base64,{base64_data}" width="{new_width}" height="{new_height}"/>'
            self.text_editor.insertHtml(image_html)
            self.text_editor.insertPlainText("\n") # Add a newline after the image

    def insert_image_from_file(self):
        """Opens a file dialog to select and insert an image."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image File", "",
                                                   "Images (*.png *.jpg *.jpeg *.gif);;All Files (*)", options=options)
        if file_path:
            self.insert_image_into_editor(image_path=file_path)

    def dragEnterEvent(self, event):
        """Handle drag enter event to accept image files."""
        # This method needs to be overridden on the QTextEdit instance itself,
        # not the QMainWindow. However, for simplicity and to keep the logic
        # in one place, we'll keep it here and assign it as a method on the widget.
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile() and url.toLocalFile().lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        """Handle drop event to insert image."""
        # Similar to dragEnterEvent, this should ideally be overridden on the QTextEdit.
        # Keeping it here and assigning it to the instance for simplicity.
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        self.insert_image_into_editor(image_path=file_path)
                        event.acceptProposedAction()
                        return
        event.ignore()

    def export_news(self):
        headline = self.headline_input.text().strip()
        category = self.category_combo.currentText()
        editor_html = self.text_editor.toHtml()

        if not headline or not editor_html:
            QMessageBox.warning(self, "Export Error", "Headline and content cannot be empty.")
            return

        unique_id = uuid.uuid4().hex
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        date = now.strftime("%Y-%m-%d")
        time_only = now.strftime("%H:%M:%S")

        # Extract summary and first image for JSON
        # This requires parsing the HTML content
        doc = QTextDocument()
        doc.setHtml(editor_html)

        # Get plain text for summary
        plain_text = doc.toPlainText()
        summary = plain_text[:200] + '...' if len(plain_text) > 200 else plain_text

        # Find first image source (base64)
        img_base64 = ""
        # QTextDocument doesn't directly expose image sources from HTML.
        # We'll need to parse the HTML string to find the first img src.
        # A simple regex or BeautifulSoup could be used here for robustness.
        # For simplicity, let's assume the first <img> tag's src is what we need.
        import re
        match = re.search(r'<img[^>]+src="([^">]+)"', editor_html)
        if match:
            img_base64 = match.group(1)


        # Ensure category directory exists
        category_dir = os.path.join(NEWS_BASE_DIR, category)
        os.makedirs(category_dir, exist_ok=True)

        # Construct the full HTML content for the individual news page
        full_html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(headline)}</title>
<style>
body {{
    font-family: 'Inter', sans-serif; /* Using Inter font */
    background: #f9f9f9;
    color: #222;
    padding: 20px;
}}
header {{
    background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
    color: white;
    padding: 20px;
    text-align: center;
    border-radius: 8px; /* Rounded corners */
}}
footer {{
    background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
    color: white;
    text-align: center;
    padding: 10px;
    margin-top: 40px;
    border-radius: 8px; /* Rounded corners */
}}
.container {{
    max-width: 800px;
    margin: auto;
    padding: 20px;
    background: #fff;
    border-radius: 8px; /* Rounded corners */
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}}
img {{
    display: block;
    margin: 20px auto;
    max-width: 90%;
    height: auto;
    border-radius: 8px; /* Rounded corners */
}}
p {{
    text-align: justify;
    margin-bottom: 16px;
}}
.date-line {{
    font-weight: bold;
    font-style: italic;
    margin: 20px 0;
}}
/* Tailwind-like rounded corners for consistency */
.rounded-lg {{ border-radius: 0.5rem; }}
.shadow-lg {{ box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05); }}
</style>
</head>
<body>
<header>
  <h1>Classic News</h1>
</header>
<div class="container">
  <p class="date-line">{timestamp}</p>
  <h2>{escape(headline)}</h2>
  {editor_html}
</div>
<footer>&copy; 2025 Classic News | Educational Demo</footer>
</body>
</html>"""

        # Save the individual HTML file
        html_filename = os.path.join(category_dir, f"{unique_id}.html")
        try:
            with open(html_filename, "w", encoding="utf-8") as f:
                f.write(full_html_content)
        except Exception as e:
            QMessageBox.critical(self, "File Save Error", f"Could not save HTML file: {e}")
            return

        # Update the central News.json file
        json_path = os.path.join(NEWS_BASE_DIR, "News.json")
        news_entry = {
            "img": img_base64,
            "title": headline,
            "summary": summary,
            "category": category,
            "date": date,
            "Time": time_only
        }

        data = []
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as jf:
                    data = json.load(jf)
                    if not isinstance(data, list):
                        data = []
            except json.JSONDecodeError:
                data = []

        data.append(news_entry)

        try:
            with open(json_path, "w", encoding="utf-8") as jf:
                json.dump(data, jf, indent=4)
            QMessageBox.information(self, "Success", "News exported and JSON updated successfully!")
            self.clear_editor()
        except Exception as e:
            QMessageBox.critical(self, "JSON Save Error", f"Could not update News.json: {e}")

    def clear_editor(self):
        self.headline_input.clear()
        self.category_combo.setCurrentIndex(0)
        self.text_editor.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = AdvancedNewsEditorApp()
    editor.show()
    sys.exit(app.exec_())
