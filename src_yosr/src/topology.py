from PyQt5.QtWidgets import (
    QWidget, QGraphicsView, QGraphicsScene, QVBoxLayout,
    QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsTextItem, QGraphicsPixmapItem
)
from PyQt5.QtGui import QPen, QBrush, QColor, QPixmap, QPainter
from PyQt5.QtCore import Qt


class ZoomableView(QGraphicsView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._zoom = 0
        self.setRenderHints(self.renderHints() | QPainter.Antialiasing)

    def wheelEvent(self, event):
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
            self._zoom += 1
        else:
            zoom_factor = zoom_out_factor
            self._zoom -= 1

        if self._zoom < -10:  # min zoom
            self._zoom = -10
            return
        if self._zoom > 20:   # max zoom
            self._zoom = 20
            return

        self.scale(zoom_factor, zoom_factor)


class TopologyWindow(QWidget):
    def __init__(self, users, aps, assignments, intermediates):
        super().__init__()
        self.setWindowTitle("Network Topology")
        self.showMaximized()

        layout = QVBoxLayout(self)
        self.view = ZoomableView()
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        layout.addWidget(self.view)

        self.draw_topology(users, aps, assignments, intermediates)

    def generate_ap_colors(self, aps):
        ap_colors = {}
        n = len(aps)
        for i, ap in enumerate(aps):
            hue = int(360 * i / max(1, n))
            color = QColor()
            color.setHsv(hue, 180, 220)
            ap_colors[ap["Name"]] = color
        return ap_colors

    def draw_topology(self, users, aps, assignments, intermediates):
        if not users or not aps:
            return

        all_x = [u["X"] for u in users] + [a["X"] for a in aps]
        all_y = [u["Y"] for u in users] + [a["Y"] for a in aps]

        X_min, X_max = min(all_x), max(all_x)
        Y_min, Y_max = min(all_y), max(all_y)

        scene_width, scene_height = 1200, 800
        s_x = scene_width / (X_max - X_min) if X_max != X_min else 1
        s_y = scene_height / (Y_max - Y_min) if Y_max != Y_min else 1
        s = min(s_x, s_y)

        x_offset = (scene_width - (X_max - X_min) * s) / 2
        y_offset = (scene_height - (Y_max - Y_min) * s) / 2

        # --- Use real coverage radius from intermediates ---
        D_max = intermediates.get("D_max", 30)  # real distance units
        ap_radius_px = D_max * s  # scale to pixels

        ap_icon = QPixmap(r"C:\Bureau\Documenten\RT3\Info\Recherche operationnelle\project\ro-matching\src_yosr\screenshots\image-removebg-preview.png")
        user_icon = QPixmap(r"C:\Bureau\Documenten\RT3\Info\Recherche operationnelle\project\ro-matching\src_yosr\screenshots\Copilot_20251127_214136-removebg-preview.png")
        ap_icon = ap_icon.scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        user_icon = user_icon.scaled(45, 45, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        ap_colors = self.generate_ap_colors(aps)

        # --- Draw APs ---
        for ap in aps:
            name = ap["Name"]
            x = (ap["X"] - X_min) * s + x_offset
            y = (ap["Y"] - Y_min) * s + y_offset

            # Coverage circle with real distance scaling
            circle = QGraphicsEllipseItem(
                x - ap_radius_px, y - ap_radius_px, 2 * ap_radius_px, 2 * ap_radius_px
            )
            circle.setBrush(QBrush(QColor(225, 190, 231, 50)))
            circle.setPen(QPen(QColor("#6a1b9a"), 2))
            self.scene.addItem(circle)

            # AP square, icon, labels as before
            square_size = 60
            rect = QGraphicsRectItem(x - square_size / 2, y - square_size / 2, square_size, square_size)
            rect.setBrush(QBrush(ap_colors[name]))
            rect.setPen(QPen(Qt.black, 2))
            self.scene.addItem(rect)

            ap_item = QGraphicsPixmapItem(ap_icon)
            ap_item.setPos(x - ap_icon.width() / 2, y - ap_icon.height() / 2)
            self.scene.addItem(ap_item)

            name_text = QGraphicsTextItem(name)
            name_text.setDefaultTextColor(Qt.black)
            name_text.setPos(x - square_size / 2, y - square_size / 2 - 20)
            self.scene.addItem(name_text)

            channel_text = QGraphicsTextItem(f"Ch {ap['Channel']}")
            channel_text.setDefaultTextColor(Qt.black)
            channel_text.setPos(x - square_size / 2, y + square_size / 2 + 5)
            self.scene.addItem(channel_text)

        # --- Draw Users ---
        for user in users:
            uname = user["Name"]
            x = (user["X"] - X_min) * s + x_offset
            y = (user["Y"] - Y_min) * s + y_offset

            assigned_ap = None
            for ap_name, user_list in assignments.items():
                if uname in user_list:
                    assigned_ap = ap_name
                    break

            if assigned_ap:
                square_size = 40
                rect = QGraphicsRectItem(x - square_size / 2, y - square_size / 2, square_size, square_size)
                rect.setBrush(QBrush(ap_colors[assigned_ap]))
                rect.setPen(QPen(Qt.black, 1))
                self.scene.addItem(rect)

            user_item = QGraphicsPixmapItem(user_icon)
            user_item.setPos(x - user_icon.width() / 2, y - user_icon.height() / 2)
            self.scene.addItem(user_item)

            label = QGraphicsTextItem(uname)
            label.setDefaultTextColor(Qt.black)
            label.setPos(x - user_icon.width() / 2, y - user_icon.height() / 2 - 20)
            self.scene.addItem(label)

            priority_text = QGraphicsTextItem(user.get("Priority", ""))
            priority_text.setDefaultTextColor(QColor("#424242"))
            priority_text.setPos(x - user_icon.width() / 2, y + user_icon.height() / 2 + 5)
            self.scene.addItem(priority_text)
