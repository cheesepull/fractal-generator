import sys
import time
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets

import fkernel 


RES_X = 1200
RES_Y = 900
MAX_ITER = 1024
DEBOUNCE_MS = 10



class FractalViewBox(pg.ViewBox):
    def __init__(self, viewer):
        super().__init__()
        self.viewer = viewer
        self.setMouseEnabled(x=False, y=False)
        self.setMenuEnabled(False)

    def wheelEvent(self, ev, axis=None):
        ev.accept()
        delta = ev.delta()
        if delta == 0:
            return
        factor = 1.15 if delta > 0 else 1.0 / 1.15
        pos = self.mapSceneToView(ev.scenePos())
        self.viewer.zoom_at(pos.x(), pos.y(), factor)

    def mouseDragEvent(self, ev, axis=None):
        if ev.button() != QtCore.Qt.LeftButton:
            ev.ignore()
            return
        ev.accept()
        p1 = self.mapSceneToView(ev.lastScenePos())
        p2 = self.mapSceneToView(ev.scenePos())
        self.viewer.pan_by(p2.x() - p1.x(), p2.y() - p1.y())



class FractalViewer(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("fkernel.mandelbrot_2")
        self.resize(1024, 800)

        self.center_x = -0.5
        self.center_y = 0.0
        self.zoom = 1.0
        self.max_iter = MAX_ITER

        self.buffer = np.zeros((RES_Y, RES_X), dtype=np.int32)

        self.colormap = pg.colormap.get('inferno')
        self._rebuild_lut()

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        vbox = QtWidgets.QVBoxLayout(central)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        self.view = pg.GraphicsView()
        vbox.addWidget(self.view, 1)

        self.vb = FractalViewBox(self)
        self.view.setCentralItem(self.vb)
        self.vb.setAspectLocked(True)

        self.img = pg.ImageItem(axisOrder='row-major')
        self.vb.addItem(self.img)

        self.info = QtWidgets.QLabel()
        self.info.setStyleSheet(
            "background:#111; color:#ddd; padding:4px; font-family:monospace;"
        )
        vbox.addWidget(self.info)

        # ---- debounce-таймер ----
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.redraw)

        # ---- статистика ----
        self._render_ms = 0.0

        QtCore.QTimer.singleShot(0, self.redraw)

    def _rebuild_lut(self):
        self.lut = self.colormap.getLookupTable(
            nPts=self.max_iter + 1, alpha=True, mode='byte'
        )


    def _extent(self):
        half_h = 1.0 / self.zoom                 
        half_w = half_h * RES_X / RES_Y         
        return (self.center_x - half_w,
                self.center_y - half_h,
                2.0 * half_w,
                2.0 * half_h)


    def zoom_at(self, px, py, factor):
        new_zoom = max(1e-9, min(self.zoom * factor, 1e15))
        ratio = self.zoom / new_zoom
        self.center_x = px - (px - self.center_x) * ratio
        self.center_y = py - (py - self.center_y) * ratio
        self.zoom = new_zoom
        self.timer.start(DEBOUNCE_MS)

    def pan_by(self, dx, dy):
        self.center_x -= dx
        self.center_y -= dy
        self.timer.start(DEBOUNCE_MS)

    def redraw(self):
        t0 = time.perf_counter()

        fkernel.mandelbrot_2(
            self.buffer, RES_X, RES_Y, self.max_iter,
            self.center_x, self.center_y, self.zoom,
        )

        rgba = self.lut[self.buffer[::-1]]      # (H, W, 4) uint8

        x, y, w, h = self._extent()
        self.img.setImage(rgba, autoLevels=False)
        self.img.setRect(QtCore.QRectF(x, y, w, h))

        self.vb.setRange(xRange=(x, x + w),
                         yRange=(y, y + h),
                         padding=0)

        t1 = time.perf_counter()
        self._render_ms = (t1 - t0) * 1000.0

        self.info.setText(
            f"center=({self.center_x:+.12f}, {self.center_y:+.12f})  "
            f"zoom={self.zoom:.4e}  iter={self.max_iter}  "
            f"render={self._render_ms:6.1f} ms  "
            f"res={RES_X}x{RES_Y}"
        )

    def keyPressEvent(self, ev):
        k = ev.key()
        if k == QtCore.Qt.Key_R:
            self.center_x = -0.5
            self.center_y = 0.0
            self.zoom = 1.0
            self.timer.start(DEBOUNCE_MS)
        elif k in (QtCore.Qt.Key_Plus, QtCore.Qt.Key_Equal):
            self.max_iter = min(self.max_iter * 2, 4096)
            self._rebuild_lut()
            self.timer.start(DEBOUNCE_MS)
        elif k == QtCore.Qt.Key_Minus:
            self.max_iter = max(self.max_iter // 2, 32)
            self._rebuild_lut()
            self.timer.start(DEBOUNCE_MS)
        else:
            super().keyPressEvent(ev)

def main():
    app = QtWidgets.QApplication(sys.argv)
    viewer = FractalViewer()
    viewer.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
