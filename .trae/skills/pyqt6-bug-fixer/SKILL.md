---
name: "pyqt6-bug-fixer"
description: "Fixes PyQt6 application bugs following MVVM architecture. Invoke when user reports bugs, crashes, or unexpected behavior in PyQt6 app."
---

# PyQt6 Bug Fixer

This skill helps fix bugs in PyQt6 applications following strict MVVM architecture principles.

## Architecture Rules to Follow

### Core Principles
- **MVVM Pattern**: View → ViewModel → Model
- **View** must NOT directly access Service layer
- **ViewModel** must inherit from `BaseViewModel`
- **All UI updates** must come from Qt Signals
- **Background tasks** must use ThreadPool
- **No IO operations** on UI thread

## Bug Fixing Workflow

### 1. Identify the Bug Type

**UI-related bugs:**
- UI not updating
- Signals not firing
- Layout issues
- Widget state problems

**Logic bugs:**
- Data not persisting
- Business logic errors
- Service layer issues

**Threading bugs:**
- UI freezing
- Crashes from thread violations
- Race conditions

### 2. Locate the Issue

Search for relevant files:
- View layer: `app/presentation/views/`
- ViewModel layer: `app/presentation/viewmodels/`
- Service layer: `app/domain/services/`
- Model layer: `app/domain/models/`

### 3. Apply Fixes Based on Bug Type

#### UI Update Issues
**Problem**: UI not updating after data changes

**Solution**:
```python
# In ViewModel - Define signal
class MyViewModel(BaseViewModel):
    dataChanged = pyqtSignal(object)

    def update_data(self, new_data):
        # Business logic
        self._data = new_data
        # Emit signal to update UI
        self.dataChanged.emit(self._data)
```

**Common Mistakes to Avoid**:
- ❌ Directly updating UI from ViewModel
- ❌ Not emitting signals after state changes
- ❌ Calling UI methods from non-UI thread

#### Threading Issues
**Problem**: UI freezing or crashes from thread violations

**Solution**:
```python
# In ViewModel - Use ThreadPool
from PyQt6.QtCore import QThreadPool, QRunnable

class MyViewModel(BaseViewModel):
    def __init__(self):
        super().__init__()
        self._thread_pool = QThreadPool()

    def run_background_task(self):
        worker = Worker(self._heavy_operation)
        worker.signals.result.connect(self._on_result)
        self._thread_pool.start(worker)

    def _heavy_operation(self):
        # IO or CPU intensive work
        pass

    def _on_result(self, result):
        # UI update on main thread via signal
        self.resultReady.emit(result)
```

**Common Mistakes to Avoid**:
- ❌ Running IO operations on UI thread
- ❌ Updating UI from worker thread directly
- ❌ Not using ThreadPool for background tasks

#### Service Layer Violations
**Problem**: View directly calling Service

**Solution**:
```python
# ❌ WRONG - View calling Service directly
class MyView(QWidget):
    def on_button_click(self):
        data = self.service.get_data()  # VIOLATION

# ✅ CORRECT - View calling ViewModel
class MyView(QWidget):
    def __init__(self, viewmodel):
        super().__init__()
        self.viewmodel = viewmodel
        self.viewmodel.dataChanged.connect(self._update_ui)

    def on_button_click(self):
        self.viewmodel.fetch_data()  # Correct

    def _update_ui(self, data):
        # Update UI elements
        pass
```

### 4. Verify the Fix

After fixing:
1. Check if signals are properly connected
2. Ensure no direct UI updates from background threads
3. Verify ViewModel inherits from BaseViewModel
4. Confirm View only binds to signals
5. Test the specific bug scenario

## Common PyQt6 Bugs and Solutions

### Bug: AttributeError: 'NoneType' object has no attribute 'connect'
**Cause**: Trying to connect signal before widget initialization
**Fix**: Ensure signals are connected in `__init__` after super().__init__()

### Bug: QObject::setParent: Cannot set parent
**Cause**: Moving objects between threads
**Fix**: Use signals/slots for thread communication instead

### Bug: RuntimeError: wrapped C/C++ object has been deleted
**Cause**: Accessing deleted Qt objects
**Fix**: Use weak references or proper lifecycle management

### Bug: UI not updating after model change
**Cause**: Missing signal emission
**Fix**: Always emit signal after changing ViewModel state

## Debugging Tips

1. **Enable Qt Debug Output**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **Check Signal Connections**:
```python
print(f"Connected receivers: {signal.receivers(signal)}")
```

3. **Verify Thread Safety**:
```python
from PyQt6.QtCore import QThread
print(f"Current thread: {QThread.currentThread()}")
```

## Code Quality Checklist

- [ ] ViewModel inherits from BaseViewModel
- [ ] All UI updates via Qt Signals
- [ ] No direct Service access from View
- [ ] Background tasks use ThreadPool
- [ ] No IO operations on UI thread
- [ ] Signals properly connected in View
- [ ] Error handling in place
- [ ] Thread safety verified

## When to Ask for Help

If you encounter:
- Complex threading issues beyond ThreadPool
- Memory leaks in Qt objects
- Performance problems requiring profiling
- Architecture decisions affecting multiple components
