import sys
import os
import uuid
import json
import base64
import re # Import regex for parsing image HTML
from datetime import datetime, timedelta
from html import escape

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QComboBox, QPushButton, QTextEdit, QAction, QToolBar,
    QFileDialog, QMessageBox, QLabel, QDialog, QFormLayout, QSpinBox
)
from PyQt5.QtGui import QFont, QImage, QTextDocument, QTextCursor, QPixmap, QTextCharFormat, QTextImageFormat
from PyQt5.QtCore import Qt, QUrl, QMimeData, QBuffer, QIODevice

# Define the base directory for news HTML files.
# This path is relative to where the Python script is executed.
# Assuming the script is in '2.0/AI Applications/', this will save HTML files to '2.0/News/{category}/{unique_id}.html'.
NEWS_HTML_BASE_DIR = "../2.0/News" # Corrected path to be relative to the project root

class ImageResizeDialog(QDialog):
    """Dialog to get new dimensions for an image."""
    def __init__(self, current_width, current_height, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Resize Image")
        self.setModal(True)
        self.setFixedSize(300, 150) # Fixed size for the dialog

        self.layout = QFormLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)

        self.width_input = QSpinBox()
        self.width_input.setRange(1, 4000)
        self.width_input.setValue(current_width)
        self.width_input.setStyleSheet("""
            QSpinBox {
                padding: 5px;
                border: 1px solid #cccccc;
                border-radius: 5px;
                font-size: 13px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 20px;
                height: 20px;
                border: 1px solid #cccccc;
                border-radius: 3px;
                background-color: #f0f0f0;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #e0e0e0;
            }
        """)
        self.layout.addRow("Width:", self.width_input)

        self.height_input = QSpinBox()
        self.height_input.setRange(1, 4000)
        self.height_input.setValue(current_height)
        self.height_input.setStyleSheet(self.width_input.styleSheet()) # Apply same style
        self.layout.addRow("Height:", self.height_input)

        self.ok_button = QPushButton("Insert")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff; /* Blue for insert */
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
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
            "Business", "Tech", "Travel", "Art", "Environment", "Education",
            "Food", "Fashion", "Automotive", "Space", "Culture", "Lifestyle", "Gaming" # Added more categories
        ]

        self.init_ui()
        self.apply_styles() # Apply styling after UI initialization

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(25, 25, 25, 25) # More padding for overall look
        main_layout.setSpacing(20) # Increased spacing between major sections

        # --- Headline, Category, and Location ---
        form_group_layout = QFormLayout() # Use QFormLayout for labels and inputs
        form_group_layout.setSpacing(10) # Spacing between rows

        self.headline_input = QLineEdit()
        self.headline_input.setPlaceholderText("Enter news headline")
        self.headline_input.setObjectName("headlineInput")
        form_group_layout.addRow("Headline:", self.headline_input)

        self.category_combo = QComboBox()
        self.category_combo.addItems(self.categories)
        self.category_combo.setObjectName("categoryCombo")
        form_group_layout.addRow("Category:", self.category_combo)

        self.location_input = QLineEdit() # New location input
        self.location_input.setPlaceholderText("Enter news location (e.g., New York, Global)")
        self.location_input.setObjectName("locationInput")
        form_group_layout.addRow("Location:", self.location_input)

        main_layout.addLayout(form_group_layout)

        # --- Text Editor ---
        self.text_editor = QTextEdit()
        self.text_editor.setAcceptRichText(True)
        self.text_editor.setPlaceholderText("Start writing your news article here...")
        self.text_editor.setObjectName("textEditor")
        
        # Set default font to Arial and default alignment to Justify
        default_font = QFont("Arial", 14) # Changed default font to Arial
        self.text_editor.setFont(default_font)
        self.text_editor.setAlignment(Qt.AlignJustify) # Set default alignment to justified

        main_layout.addWidget(self.text_editor, 1) # Stretch factor for editor

        # Enable drag and drop for the text editor
        self.text_editor.setAcceptDrops(True)
        self.text_editor.dragEnterEvent = self.dragEnterEvent
        self.text_editor.dropEvent = self.dropEvent
        
        # Override mousePressEvent for image resizing
        # Store original method to call it within our override
        self.original_mousePressEvent = self.text_editor.mousePressEvent
        self.text_editor.mousePressEvent = self.text_editor_mousePressEvent

        # --- Toolbar ---
        toolbar = QToolBar("Editor Toolbar")
        self.addToolBar(toolbar)
        toolbar.setObjectName("editorToolbar")
        toolbar.setMovable(False)

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
        
        # Set "Arial" as default if available, otherwise the first available font
        if "Arial" in QFont().families():
            self.font_combo.setCurrentText("Arial")
        else:
            self.font_combo.setCurrentIndex(0) # Fallback to the first font in the list
        
        self.font_combo.currentTextChanged.connect(self.text_editor.setFontFamily)
        self.font_combo.setObjectName("fontCombo")
        toolbar.addWidget(self.font_combo)

        # Font Size
        self.size_combo = QComboBox(self)
        self.size_combo.addItems([str(s) for s in range(8, 73, 2)])
        self.size_combo.setCurrentText("14") # Set a larger default font size for toolbar control
        self.size_combo.currentTextChanged.connect(
            lambda s: self.text_editor.setFontPointSize(float(s))
        )
        self.size_combo.setObjectName("sizeCombo")
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
        self.export_button = QPushButton("Export News") # Made instance variable for styling and disabling
        self.export_button.setObjectName("exportButton") # Object name for styling
        self.export_button.clicked.connect(self.export_news)
        main_layout.addWidget(self.export_button, alignment=Qt.AlignCenter) # Center the button

    def apply_styles(self):
        # Global application styling using QSS (Qt Style Sheets)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f2f5; /* Light grey background for the main window */
                border-radius: 12px; /* Overall rounded corners for the window */
            }
            QToolBar#editorToolbar {
                background-color: #e0e2e5; /* Slightly darker toolbar background */
                border: none;
                padding: 8px; /* Increased padding */
                spacing: 8px; /* Increased spacing between items */
                border-radius: 10px; /* More rounded corners for toolbar */
                margin-bottom: 15px; /* More margin below toolbar */
            }
            QToolButton { /* Styles for actions (buttons) within the toolbar */
                background-color: #ffffff;
                border: 1px solid #d0d2d5;
                border-radius: 6px; /* Rounded corners for toolbar buttons */
                padding: 6px 12px; /* Increased padding */
                font-size: 13px;
                color: #333333;
                min-width: 30px; /* Ensure a minimum width */
            }
            QToolButton:hover {
                background-color: #e6e6e6;
                border-color: #a0a0a0;
            }
            QToolButton:pressed {
                background-color: #d0d0d0;
            }
            QToolButton:checked { /* For toggleable actions like bold/italic */
                background-color: #a0c0e0; /* A light blue to indicate active state */
                border-color: #6080a0;
                color: #1a1a1a;
            }
            QLabel {
                font-size: 15px; /* Increased font size for labels */
                color: #333333;
                font-weight: 600; /* Bolder labels */
            }
            QLineEdit#headlineInput, QComboBox#categoryCombo, QLineEdit#locationInput { /* Added locationInput */
                padding: 10px 15px; /* More padding */
                border: 1px solid #cccccc;
                border-radius: 10px; /* More rounded corners */
                font-size: 15px; /* Larger font */
                background-color: #ffffff;
                color: #333333;
                box-shadow: inset 0 1px 3px rgba(0,0,0,0.08); /* Inner shadow for depth */
            }
            QLineEdit#headlineInput:focus, QComboBox#categoryCombo:focus, QLineEdit#locationInput:focus { /* Added locationInput */
                border: 2px solid #5cb85c; /* Green border on focus */
                box-shadow: 0 0 8px rgba(92, 184, 92, 0.4); /* Green glow on focus */
            }
            QComboBox#categoryCombo::drop-down {
                border: 0px; /* No border for the dropdown arrow */
            }
            QComboBox#categoryCombo::down-arrow {
                image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABmJLR0QA/wD/AP+gvaeTAAAAV0lEQVQ4jWNgGAWjYBSMglEwCkYBQjAA/x8XGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGAUjAgAAnF4Y/w+7k2UAAAAASUVORK5CYII=); /* Custom dropdown arrow */
                width: 14px; /* Larger arrow */
                height: 14px;
                margin-right: 8px; /* More margin */
            }
            QTextEdit#textEditor {
                border: 1px solid #cccccc;
                border-radius: 10px; /* More rounded corners */
                padding: 15px; /* More padding inside editor */
                font-size: 15px; /* Increased font size for editor text */
                background-color: #ffffff;
                color: #333333;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08); /* Subtle shadow */
            }
            QTextEdit#textEditor:focus {
                border: 2px solid #5cb85c;
                box-shadow: 0 0 10px rgba(92, 184, 92, 0.5);
            }
            QPushButton#exportButton {
                background-color: #5cb85c; /* Green theme for export */
                color: white;
                padding: 15px 30px; /* Larger padding */
                border: none;
                border-radius: 12px; /* More rounded */
                font-size: 17px; /* Larger font */
                font-weight: bold;
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2); /* More prominent shadow */
                transition: background-color 0.3s ease, box-shadow 0.3s ease, transform 0.1s ease;
                min-width: 150px; /* Ensure decent size */
            }
            QPushButton#exportButton:hover {
                background-color: #4cae4c; /* Darker green on hover */
                box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
                transform: translateY(-3px); /* More noticeable lift effect */
            }
            QPushButton#exportButton:pressed {
                background-color: #449d44; /* Even darker on press */
                transform: translateY(0);
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.15);
            }
            QMessageBox {
                font-size: 14px;
            }
            QComboBox#fontCombo, QComboBox#sizeCombo {
                padding: 5px;
                border: 1px solid #cccccc;
                border-radius: 5px;
                font-size: 13px;
                background-color: #ffffff;
                color: #333333;
            }
            QComboBox#fontCombo::drop-down, QComboBox#sizeCombo::drop-down {
                border: 0px;
            }
            QComboBox#fontCombo::down-arrow {
                image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABmJLR0QA/wD/AP+gvaeTAAAAV0lEQVQ4jWNgGAWjYBSMglEwCkYBQjAA/x8XGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGAUjAgAAnF4Y/w+7k2UAAAAASUVORK5CYII=);
                width: 12px;
                height: 12px;
                margin-right: 5px;
            }
        """)

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
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile() and url.toLocalFile().lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        """Handle drop event to insert image."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        self.insert_image_into_editor(image_path=file_path)
                        event.acceptProposedAction()
                        return
        event.ignore()

    def text_editor_mousePressEvent(self, event):
        """Custom mouse press event for QTextEdit to handle image clicks."""
        # Call the original mousePressEvent first to maintain default behavior
        self.original_mousePressEvent(event) # Call the stored original method

        if event.button() == Qt.RightButton:
            cursor = self.text_editor.textCursor()
            # Move cursor to the position of the mouse click
            cursor.setPosition(self.text_editor.cursorForPosition(event.pos()).position())

            # Check if the cursor is over an image
            char_format = cursor.charFormat()
            if char_format.isImageFormat():
                image_format = char_format.toImageFormat()
                image_src = image_format.name() # This will be the data:image/png;base64,... string
                
                # Extract base64 data and dimensions from the src string
                if image_src.startswith("data:image/"):
                    # Extract base64 data
                    base64_data_match = re.match(r"data:image/[^;]+;base64,(.*)", image_src)
                    if base64_data_match:
                        base64_only_data = base64_data_match.group(1)
                        try:
                            decoded_image_data = base64.b64decode(base64_only_data)
                            qimage = QImage()
                            qimage.loadFromData(decoded_image_data)

                            # Show resize dialog with current dimensions
                            dialog = ImageResizeDialog(qimage.width(), qimage.height(), self)
                            if dialog.exec_() == QDialog.Accepted:
                                new_width, new_height = dialog.get_dimensions()

                                # Remove the old image
                                cursor.beginEditBlock() # Start an edit block for undo/redo
                                # To delete the image, we need to select it.
                                # An image is represented as a single character.
                                cursor.movePosition(QTextCursor.PreviousCharacter, QTextCursor.KeepAnchor)
                                cursor.deleteChar()
                                cursor.endEditBlock()

                                # Insert the new resized image
                                resized_image = qimage.scaled(new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                                buffer = QBuffer()
                                buffer.open(QIODevice.WriteOnly)
                                resized_image.save(buffer, "PNG")
                                new_base64_data = base64.b64encode(buffer.data().data()).decode("utf-8")
                                buffer.close()

                                new_image_format = QTextImageFormat()
                                new_image_format.setName(f"data:image/png;base64,{new_base64_data}")
                                new_image_format.setWidth(new_width)
                                new_image_format.setHeight(new_height)

                                self.text_editor.textCursor().insertImage(new_image_format)
                                self.text_editor.textCursor().insertPlainText("\n") # Add a newline after the image
                        except Exception as e:
                            QMessageBox.critical(self, "Image Processing Error", f"Failed to process image for resizing: {e}")
                    else:
                        QMessageBox.warning(self, "Image Error", "Could not extract base64 data from image source.")
                else:
                    QMessageBox.warning(self, "Image Error", "Clicked image is not a base64 embedded image or format is unsupported for direct editing.")


    def export_news(self):
        # Confirmation dialog
        reply = QMessageBox.question(self, 'Confirm Export',
                                     "Are you sure you want to export this news? Once exported, it cannot be edited or resubmitted.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.No:
            return

        headline = self.headline_input.text().strip()
        category = self.category_combo.currentText()
        location = self.location_input.text().strip() # Get location
        editor_html = self.text_editor.toHtml()

        # Extract only the content within the <body> tags from editor_html
        # QTextEdit.toHtml() often generates a full HTML document. We only need the body content.
        body_content_match = re.search(r'<body>(.*?)</body>', editor_html, re.DOTALL)
        if body_content_match:
            clean_editor_html = body_content_match.group(1)
        else:
            clean_editor_html = editor_html # Fallback if body tags are not found (unlikely for QTextEdit output)

        if not headline or not clean_editor_html or not location: # Validate location with cleaned HTML
            QMessageBox.warning(self, "Export Error", "Headline, content, and location cannot be empty.")
            return

        unique_id = uuid.uuid4().hex
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        date = now.strftime("%Y-%m-%d")
        time_only = now.strftime("%H:%M:%S")

        # Extract summary and first image for JSON
        doc = QTextDocument()
        doc.setHtml(editor_html) # Use original editor_html to parse for summary/image

        # Get plain text for summary
        plain_text = doc.toPlainText()
        summary = plain_text[:200] + '...' if len(plain_text) > 200 else plain_text

        # Find first image source (base64) from the original editor_html
        img_base64 = ""
        # Use regex to find the first <img> tag and its src attribute
        match = re.search(r'<img[^>]+src="([^">]+)"', editor_html)
        if match:
            img_base64 = match.group(1)

        # Ensure category directory for HTML files exists
        # This will create 'News/{category}/' relative to the script's execution directory
        category_dir = os.path.join(NEWS_HTML_BASE_DIR, category)
        try:
            os.makedirs(category_dir, exist_ok=True)
        except OSError as e:
            QMessageBox.critical(self, "Directory Creation Error",
                                 f"Failed to create directory: {category_dir}\nError: {e}\nPlease check permissions.")
            return

        # Construct the full HTML content for the individual news page
        # The style block within the HTML is designed to mimic newspaper-like content
        full_html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(headline)}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>
body {{
    font-family: 'Arial', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"; /* Changed to Arial with fallbacks for newspaper look */
    background: #f9f9f9;
    color: #222;
    text-align: justify; /* Justify text for newspaper style */
    padding: 30px; /* Increased padding for the body */
    line-height: 1.6; /* Improved line spacing for readability */
}}
header {{
    background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
    color: white;
    padding: 20px;
    text-align: center;
    border-radius: 8px; /* Rounded corners */
    margin-bottom: 30px; /* Added margin below header */
}}
footer {{
    background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
    color: white;
    text-align: center;
    padding: 15px; /* Increased padding for footer */
    margin-top: 50px; /* Increased margin above footer */
    border-radius: 8px; /* Rounded corners */
}}
.container {{
    max-width: 900px; /* Slightly wider container */
    margin: auto;
    padding: 40px; /* Increased padding inside the container */
    background: #fff;
    border-radius: 12px; /* More rounded corners for the container */
    box-shadow: 0 6px 20px rgba(0,0,0,0.15); /* More prominent shadow for depth */
}}
h2 {{
    font-size: 2.2em; /* Larger headline */
    color: #333;
    margin-bottom: 20px; /* Space below headline */
    text-align: center; /* Center the headline */
}}
.metadata-line {{ /* New class for metadata line */
    font-weight: bold;
    font-style: italic;
    margin: 15px 0 25px 0; /* Adjusted margin */
    color: #666;
    text-align: center; /* Center the metadata */
    font-size: 0.95em;
}}
img {{
    display: block;
    margin: 30px auto; /* More margin around images */
    max-width: 95%; /* Slightly larger max-width for images */
    height: auto;
    border-radius: 10px; /* More rounded corners for images */
    box-shadow: 0 4px 15px rgba(0,0,0,0.1); /* Subtle shadow for images */
}}
p {{
    text-align: justify; /* Justify paragraphs for newspaper style */
    margin-bottom: 18px; /* More space between paragraphs */
    font-size: 1.1em; /* Slightly larger paragraph text */
    color: #444;
}}
/* Tailwind-like rounded corners for consistency */
.rounded-lg {{ border-radius: 0.5rem; }}
.shadow-lg {{ box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 44px 6px -2px rgba(0, 0, 0, 0.05); }}
</style>
</head>
<body>
<header>
  <h1>Classic News</h1>
</header>
<div class="container">
  <p class="metadata-line">{location} | {timestamp}</p> <!-- Display location and timestamp -->
  <h2>{escape(headline)}</h2>
  {clean_editor_html}
</div>
<footer>&copy; 2025 Classic News | Educational Demo</footer>
</body>
</html>"""

        # Save the individual HTML file
        html_filename = os.path.join(category_dir, f"{unique_id}.html")
        try:
            with open(html_filename, "w", encoding="utf-8") as f:
                f.write(full_html_content)
            QMessageBox.information(self, "HTML Saved", f"HTML file saved successfully to:\n{os.path.abspath(html_filename)}")
        except IOError as e:
            QMessageBox.critical(self, "File Save Error",
                                 f"Failed to save HTML file: {os.path.abspath(html_filename)}\nError: {e}\nPlease check permissions.")
            return
        except Exception as e:
            QMessageBox.critical(self, "File Save Error",
                                 f"An unexpected error occurred while saving HTML: {os.path.abspath(html_filename)}\nError: {e}")
            return

        # Update the central News.json file
        # This path is relative to where the script is executed, assuming it's in 'AI Applications/'
        json_path = "Data/news.json" # Corrected path to be relative to the project root
        
        news_entry = {
            "img": img_base64,
            "title": headline,
            "summary": summary,
            "category": category,
            "date": date,
            "Time": time_only,
            "location": location, # Add location to JSON
            "uniqueId": unique_id
        }

        data = []
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as jf:
                    data = json.load(jf)
                    if not isinstance(data, list):
                        data = []
            except json.JSONDecodeError:
                QMessageBox.warning(self, "JSON Read Error",
                                    f"Could not read existing News.json file: {os.path.abspath(json_path)}\nFile might be empty or corrupted. Starting with an empty list.")
                data = []
            except Exception as e:
                QMessageBox.critical(self, "JSON Read Error",
                                     f"An unexpected error occurred while reading News.json: {os.path.abspath(json_path)}\nError: {e}")
                data = []

        data.append(news_entry)

        try:
            with open(json_path, "w", encoding="utf-8") as jf:
                json.dump(data, jf, indent=4)
            
            QMessageBox.information(self, "JSON Updated", "News.json updated successfully!")
            
            # Disable editing after export
            self.headline_input.setEnabled(False)
            self.category_combo.setEnabled(False)
            self.location_input.setEnabled(False) # Disable location input
            self.text_editor.setEnabled(False)
            self.export_button.setEnabled(False)
            
            # Close the application
            self.close()

        except Exception as e:
            QMessageBox.critical(self, "JSON Save Error", f"Could not update News.json: {os.path.abspath(json_path)}\nError: {e}")

    def clear_editor(self):
        # This method is now primarily for initial setup or if you wanted to reset without closing
        self.headline_input.clear()
        self.category_combo.setCurrentIndex(0)
        self.location_input.clear() # Clear location input
        self.text_editor.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Maximize application font size
    font = QFont()
    font.setPointSize(14) # Set a larger default font size for the entire application
    app.setFont(font)

    editor = AdvancedNewsEditorApp()
    editor.show()
    sys.exit(app.exec_())
