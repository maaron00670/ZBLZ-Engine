"""
ZBLZ Engine - Process List Widget
Displays running processes for selection.

Prepared for future features:
- Real process scanning
- Process filtering
- Wine/Proton process detection
"""

from typing import List, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton,
    QGroupBox, QLineEdit, QCheckBox
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QColor, QBrush

from models.app_state import ProcessInfo


class ProcessListWidget(QWidget):
    """
    Widget for displaying and selecting processes.
    
    Signals:
        process_selected: Emitted when a process is selected (ProcessInfo)
        refresh_requested: Emitted when refresh button is clicked
        attach_requested: Emitted when attach button is clicked
    """
    
    process_selected = pyqtSignal(object)  # ProcessInfo
    refresh_requested = pyqtSignal(bool)   # games_only parameter
    attach_requested = pyqtSignal()
    detach_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._processes: List[ProcessInfo] = []
        self._selected: Optional[ProcessInfo] = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Initialize the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        group = QGroupBox("Process List")
        group_layout = QVBoxLayout(group)
        
        # Filter row with games only checkbox
        filter_row = QHBoxLayout()
        
        self._games_only_checkbox = QCheckBox("Games only (uncheck = all user processes)")
        self._games_only_checkbox.setChecked(True)
        filter_row.addWidget(self._games_only_checkbox)
        
        filter_row.addStretch()
        
        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.setMinimumWidth(100)
        self._refresh_btn.clicked.connect(self._on_refresh_clicked)
        filter_row.addWidget(self._refresh_btn)
        
        group_layout.addLayout(filter_row)
        
        # Search/filter row
        filter_layout = QHBoxLayout()
        
        self._filter_input = QLineEdit()
        self._filter_input.setPlaceholderText("Filter by name or PID...")
        self._filter_input.textChanged.connect(self._apply_filter)
        filter_layout.addWidget(self._filter_input)
        
        group_layout.addLayout(filter_layout)
        
        # Process list
        self._list_widget = QListWidget()
        self._list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        self._list_widget.itemDoubleClicked.connect(
            lambda: self.attach_requested.emit()
        )
        group_layout.addWidget(self._list_widget)
        
        # Info label
        self._info_label = QLabel("Double-click to attach (future feature)")
        self._info_label.setObjectName("subtitle")
        group_layout.addWidget(self._info_label)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self._attach_btn = QPushButton("Attach")
        self._attach_btn.setEnabled(False)
        self._attach_btn.clicked.connect(self.attach_requested.emit)
        button_layout.addWidget(self._attach_btn)
        
        self._detach_btn = QPushButton("Detach")
        self._detach_btn.setEnabled(False)
        self._detach_btn.clicked.connect(self.detach_requested.emit)
        button_layout.addWidget(self._detach_btn)
        
        button_layout.addStretch()
        group_layout.addLayout(button_layout)
        
        layout.addWidget(group)
    
    def _on_refresh_clicked(self):
        """Handle refresh button click."""
        games_only = self._games_only_checkbox.isChecked()
        self.refresh_requested.emit(games_only)
    
    def _on_selection_changed(self):
        """Handle list selection changes."""
        items = self._list_widget.selectedItems()
        if items:
            index = self._list_widget.row(items[0])
            # Find the actual process from filtered view
            visible_processes = self._get_visible_processes()
            if 0 <= index < len(visible_processes):
                self._selected = visible_processes[index]
                self._attach_btn.setEnabled(True)
                self.process_selected.emit(self._selected)
        else:
            self._selected = None
            self._attach_btn.setEnabled(False)
    
    def _get_visible_processes(self) -> List[ProcessInfo]:
        """Get processes matching the current filter."""
        filter_text = self._filter_input.text().lower()
        if not filter_text:
            return self._processes
        return [
            p for p in self._processes
            if filter_text in p.name.lower() or filter_text in str(p.pid)
        ]
    
    def _apply_filter(self, text: str):
        """Apply filter to the process list."""
        self._update_list_display()
    
    def _update_list_display(self):
        """Update the list widget with current processes and filter."""
        self._list_widget.clear()
        
        visible = self._get_visible_processes()
        
        for process in visible:
            # Create descriptive item text
            tags = []
            if process.is_hooked:
                tags.append("SPEEDHACK ACTIVE")
            if process.is_wine_process:
                tags.append("WINE")
            if process.is_proton_process:
                tags.append("PROTON")
            
            tag_str = f" [{', '.join(tags)}]" if tags else ""
            
            # Show process name and relevant part of cmdline
            display_name = process.name
            if process.cmdline and process.cmdline != process.name:
                # Try to extract game name from cmdline
                cmdline_short = process.cmdline[:80]
                if len(process.cmdline) > 80:
                    cmdline_short += "..."
                item_text = f"[{process.pid}] {display_name}{tag_str}\n    {cmdline_short}"
            else:
                item_text = f"[{process.pid}] {display_name}{tag_str}"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, process)  # Store process object
            
            # Highlight processes with speedhack active
            if process.is_hooked:
                item.setForeground(QBrush(QColor("#4ade80")))  # Green color
            
            self._list_widget.addItem(item)
        
        # Update info label
        total = len(self._processes)
        shown = len(visible)
        if total == 0:
            self._info_label.setText("No processes found. Click Refresh to scan.")
        elif shown < total:
            self._info_label.setText(f"Showing {shown} of {total} processes")
        else:
            self._info_label.setText(f"{total} processes found")
    
    def set_processes(self, processes: List[ProcessInfo]):
        """Update the process list."""
        self._processes = processes
        self._selected = None
        self._attach_btn.setEnabled(False)
        self._update_list_display()
    
    def get_selected(self) -> Optional[ProcessInfo]:
        """Get the currently selected process."""
        return self._selected
    
    def clear(self):
        """Clear the process list."""
        self._processes = []
        self._selected = None
        self._list_widget.clear()
        self._attach_btn.setEnabled(False)
        self._info_label.setText("No processes loaded")
    
    def set_attached(self, is_attached: bool, pid: int = None):
        """Update UI to reflect attachment state."""
        self._attach_btn.setEnabled(not is_attached and self._selected is not None)
        self._detach_btn.setEnabled(is_attached)
        
        if is_attached and pid:
            self._info_label.setText(f"Attached to PID {pid} - Speed changes apply in real-time!")
            self._info_label.setStyleSheet("color: #4ade80;")  # Green
        else:
            self._info_label.setStyleSheet("")
            self._update_list_display()
