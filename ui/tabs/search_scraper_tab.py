"""
Search Scraper Tab

Web search scraper with multiple search engines.
⚠️ Use responsibly - may violate TOS and result in temporary bans.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QTextBrowser, QComboBox, QSpinBox, QCheckBox,
    QGroupBox, QMessageBox, QFileDialog, QProgressBar
)

try:
    from search_engines import Google, Bing, Yahoo, Duckduckgo, Aol, Mojeek
    SEARCH_ENGINES_AVAILABLE = True
except ImportError:
    SEARCH_ENGINES_AVAILABLE = False


class SearchWorker(QObject):
    """Worker for running searches in background thread."""
    
    finished = Signal(list)
    error = Signal(str)
    progress = Signal(str)
    
    def __init__(self, engine_name: str, query: str, pages: int, proxy: Optional[str] = None):
        super().__init__()
        self.engine_name = engine_name
        self.query = query
        self.pages = pages
        self.proxy = proxy
    
    def run(self):
        """Execute the search."""
        try:
            # Map engine names to classes
            engines = {
                'Google': Google,
                'Bing': Bing,
                'Yahoo': Yahoo,
                'DuckDuckGo': Duckduckgo,
                'AOL': Aol,
                'Mojeek': Mojeek
            }
            
            if self.engine_name not in engines:
                self.error.emit(f"Unknown engine: {self.engine_name}")
                return
            
            self.progress.emit(f"🔍 Searching {self.engine_name}...")
            
            # Create engine instance
            engine_class = engines[self.engine_name]
            engine = engine_class(proxy=self.proxy, timeout=15)
            
            # Perform search
            self.progress.emit(f"📄 Fetching {self.pages} page(s)...")
            results = engine.search(self.query, pages=self.pages)
            
            # Extract links
            links = results.links()
            
            self.progress.emit(f"✅ Found {len(links)} results")
            self.finished.emit(links)
            
        except Exception as e:
            self.error.emit(f"Search failed: {str(e)}")


class SearchScraperTab(QWidget):
    """Tab for web search scraping."""
    
    def __init__(self):
        super().__init__()
        self._worker = None
        self._thread = None
        self._results = []
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Warning banner
        warning = QLabel("⚠️ WARNING: Web scraping may violate search engine TOS and result in temporary bans. Use responsibly!")
        warning.setStyleSheet("""
            QLabel {
                background-color: #FF6B6B;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
        """)
        warning.setWordWrap(True)
        layout.addWidget(warning)
        
        # Check if library is available
        if not SEARCH_ENGINES_AVAILABLE:
            error_label = QLabel("❌ Search engines library not installed!\n\nRun: pip install -e Search-Engines-Scraper-master")
            error_label.setStyleSheet("color: #FF6B6B; padding: 20px; font-size: 14px;")
            layout.addWidget(error_label)
            return
        
        # Search configuration
        config_group = QGroupBox("🔍 Search Configuration")
        config_layout = QVBoxLayout()
        
        # Query input
        query_layout = QHBoxLayout()
        query_layout.addWidget(QLabel("Query:"))
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Enter your search query...")
        query_layout.addWidget(self.query_input)
        config_layout.addLayout(query_layout)
        
        # Engine selection
        engine_layout = QHBoxLayout()
        engine_layout.addWidget(QLabel("Search Engine:"))
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(['Google', 'Bing', 'Yahoo', 'DuckDuckGo', 'AOL', 'Mojeek'])
        engine_layout.addWidget(self.engine_combo)
        
        engine_layout.addWidget(QLabel("Pages:"))
        self.pages_spin = QSpinBox()
        self.pages_spin.setMinimum(1)
        self.pages_spin.setMaximum(5)  # Limit to 5 pages to avoid bans
        self.pages_spin.setValue(1)
        self.pages_spin.setToolTip("⚠️ More pages = higher ban risk!")
        engine_layout.addWidget(self.pages_spin)
        
        config_layout.addLayout(engine_layout)
        
        # Proxy settings
        proxy_layout = QHBoxLayout()
        self.use_proxy_check = QCheckBox("Use Proxy (recommended)")
        self.use_proxy_check.setToolTip("Using a proxy reduces ban risk")
        proxy_layout.addWidget(self.use_proxy_check)
        
        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("http://proxy:port or socks5://proxy:port")
        self.proxy_input.setEnabled(False)
        self.use_proxy_check.toggled.connect(self.proxy_input.setEnabled)
        proxy_layout.addWidget(self.proxy_input)
        config_layout.addLayout(proxy_layout)
        
        # Safety delay
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("⏱️ Delay between requests:"))
        self.delay_spin = QSpinBox()
        self.delay_spin.setMinimum(1)
        self.delay_spin.setMaximum(10)
        self.delay_spin.setValue(3)
        self.delay_spin.setSuffix(" seconds")
        self.delay_spin.setToolTip("Longer delays reduce ban risk")
        delay_layout.addWidget(self.delay_spin)
        delay_layout.addStretch()
        config_layout.addLayout(delay_layout)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Search button
        button_layout = QHBoxLayout()
        self.search_btn = QPushButton("🔍 Search")
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #666;
            }
        """)
        self.search_btn.clicked.connect(self._start_search)
        button_layout.addWidget(self.search_btn)
        
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_search)
        button_layout.addWidget(self.stop_btn)
        
        layout.addLayout(button_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #888; padding: 5px;")
        layout.addWidget(self.status_label)
        
        # Results area
        results_group = QGroupBox("📊 Results")
        results_layout = QVBoxLayout()
        
        # Results count
        self.results_count_label = QLabel("No results yet")
        self.results_count_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        results_layout.addWidget(self.results_count_label)
        
        # Results text area with clickable links
        self.results_text = QTextBrowser()  # Changed from QTextEdit to support clickable links
        self.results_text.setOpenExternalLinks(True)  # Enable clicking links
        self.results_text.setPlaceholderText("Search results will appear here as clickable links...")
        self.results_text.setStyleSheet("""
            QTextBrowser {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: 1px solid #3E3E3E;
                border-radius: 4px;
                padding: 10px;
                font-size: 12px;
                font-family: 'Consolas', monospace;
            }
            QTextBrowser a {
                color: #4A9EFF;
                text-decoration: underline;
            }
            QTextBrowser a:hover {
                color: #6BB6FF;
            }
        """)
        results_layout.addWidget(self.results_text)
        
        # Export buttons
        export_layout = QHBoxLayout()
        
        btn_copy = QPushButton("📋 Copy All")
        btn_copy.clicked.connect(self._copy_results)
        export_layout.addWidget(btn_copy)
        
        btn_save_txt = QPushButton("💾 Save as TXT")
        btn_save_txt.clicked.connect(lambda: self._save_results('txt'))
        export_layout.addWidget(btn_save_txt)
        
        btn_save_json = QPushButton("💾 Save as JSON")
        btn_save_json.clicked.connect(lambda: self._save_results('json'))
        export_layout.addWidget(btn_save_json)
        
        btn_save_csv = QPushButton("💾 Save as CSV")
        btn_save_csv.clicked.connect(lambda: self._save_results('csv'))
        export_layout.addWidget(btn_save_csv)
        
        btn_clear = QPushButton("🗑️ Clear")
        btn_clear.clicked.connect(self._clear_results)
        export_layout.addWidget(btn_clear)
        
        results_layout.addLayout(export_layout)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
    
    def _start_search(self):
        """Start the search."""
        query = self.query_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Error", "Please enter a search query!")
            return
        
        # Confirm if using many pages
        pages = self.pages_spin.value()
        if pages > 2:
            reply = QMessageBox.question(
                self,
                "⚠️ Ban Risk Warning",
                f"Scraping {pages} pages increases the risk of getting temporarily banned.\n\n"
                "Are you sure you want to continue?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # Get proxy if enabled
        proxy = None
        if self.use_proxy_check.isChecked():
            proxy = self.proxy_input.text().strip() or None
        
        # Disable UI
        self.search_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        
        # Create worker
        engine = self.engine_combo.currentText()
        self._worker = SearchWorker(engine, query, pages, proxy)
        self._thread = threading.Thread(target=self._worker.run, daemon=True)
        
        # Connect signals
        self._worker.finished.connect(self._on_search_finished)
        self._worker.error.connect(self._on_search_error)
        self._worker.progress.connect(self._on_search_progress)
        
        # Start search
        self._thread.start()
    
    def _stop_search(self):
        """Stop the search."""
        if self._thread and self._thread.is_alive():
            # Can't really stop thread cleanly, just disable UI
            self.status_label.setText("⚠️ Stopping... (may take a moment)")
        self._reset_ui()
    
    def _on_search_finished(self, links: list):
        """Handle search completion."""
        self._results = links
        
        # Display results
        if links:
            self.results_count_label.setText(f"✅ Found {len(links)} results")
            
            # Format links as clickable HTML
            html_links = []
            for i, link in enumerate(links, 1):
                html_links.append(f'{i}. <a href="{link}">{link}</a>')
            
            self.results_text.setHtml('<br>'.join(html_links))
            self.status_label.setText(f"✅ Search complete! Found {len(links)} clickable links")
        else:
            self.results_count_label.setText("⚠️ No results found")
            self.results_text.setPlainText("No results found. Try a different query or search engine.")
            self.status_label.setText("⚠️ No results found")
        
        self._reset_ui()
    
    def _on_search_error(self, error: str):
        """Handle search error."""
        self.status_label.setText(f"❌ Error: {error}")
        QMessageBox.critical(self, "Search Error", f"Search failed:\n\n{error}")
        self._reset_ui()
    
    def _on_search_progress(self, message: str):
        """Handle progress update."""
        self.status_label.setText(message)
    
    def _reset_ui(self):
        """Reset UI to ready state."""
        self.search_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
    
    def _copy_results(self):
        """Copy results to clipboard."""
        if not self._results:
            QMessageBox.warning(self, "No Results", "No results to copy!")
            return
        
        import pyperclip
        pyperclip.copy('\n'.join(self._results))
        self.status_label.setText(f"✅ Copied {len(self._results)} links to clipboard!")
    
    def _save_results(self, format: str):
        """Save results to file."""
        if not self._results:
            QMessageBox.warning(self, "No Results", "No results to save!")
            return
        
        # Get save path
        filters = {
            'txt': "Text Files (*.txt)",
            'json': "JSON Files (*.json)",
            'csv': "CSV Files (*.csv)"
        }
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Results",
            f"search_results.{format}",
            filters.get(format, "All Files (*.*)")
        )
        
        if not file_path:
            return
        
        try:
            if format == 'txt':
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(self._results))
            
            elif format == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'query': self.query_input.text(),
                        'engine': self.engine_combo.currentText(),
                        'count': len(self._results),
                        'results': self._results
                    }, f, indent=2)
            
            elif format == 'csv':
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['URL'])
                    for link in self._results:
                        writer.writerow([link])
            
            self.status_label.setText(f"✅ Saved {len(self._results)} results to {file_path}")
            QMessageBox.information(self, "Success", f"Results saved to:\n{file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save results:\n\n{str(e)}")
    
    def _clear_results(self):
        """Clear results."""
        self._results = []
        self.results_text.clear()
        self.results_count_label.setText("No results yet")
        self.status_label.setText("Ready")
