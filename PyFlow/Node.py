from Settings import *
from Qt import QtCore
from Qt import QtGui
from Qt.QtWidgets import QGraphicsTextItem
from Qt.QtWidgets import QGraphicsItem
from Qt.QtWidgets import QLabel
from Qt.QtWidgets import QGraphicsWidget
from Qt.QtWidgets import QGraphicsProxyWidget
from Qt.QtWidgets import QGraphicsLinearLayout
from Qt.QtWidgets import QSizePolicy
from Qt.QtWidgets import QStyle
from Port import Port, getPortColorByType
from AbstractGraph import *
from types import MethodType
from PinInputWidgets import getPinWidget
from inspect import getargspec


class NodeName(QGraphicsTextItem):
    def __init__(self, parent):
        QGraphicsTextItem.__init__(self)
        self.object_type = ObjectTypes.NodeName
        self.setParentItem(parent)
        self.options = self.parentItem().graph().get_settings()
        self.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.desc = parent.description()
        self.descFontPen = QtGui.QPen(QtCore.Qt.gray, 0.5)
        self.h = self.boundingRect().height()
        if self.options:
            self.text_color = QtGui.QColor(self.options.value('NODES/Nodes label font color'))
            self.setDefaultTextColor(self.text_color)
            self.opt_font = QtGui.QFont(self.options.value('NODES/Nodes label font'))
            self.opt_font_size = int(self.options.value('NODES/Nodes label font size'))
            self.opt_font.setPointSize(self.opt_font_size)
            self.setFont(self.opt_font)
        self.descFont = QtGui.QFont("Consolas", self.opt_font.pointSize() / 2.0, 2, True)
        self.setPos(0, -self.boundingRect().height() - 8)
        self.color = QtGui.QColor(0, 255, 50, 100)
        self.clipRect = None
        self.roundCornerFactor = 1.0
        self.bg = QtGui.QImage(':/icons/resources/white.png')
        self.icon = None

    @staticmethod
    def IsRenamable():
        return False

    def keyPressEvent(self, event):
        key = event.key()
        if (key == QtCore.Qt.Key_Return) or (key == QtCore.Qt.Key_Escape):
            self.setEnabled(False)
            self.setEnabled(True)
            return
        else:
            QGraphicsTextItem.keyPressEvent(self, event)

    def boundingRect(self):
        return QtCore.QRectF(0, 0, self.parentItem().w, 25)

    def paint(self, painter, option, widget):
        r = QtCore.QRectF(option.rect)
        r.setWidth(self.parentItem().childrenBoundingRect().width() - 0.25)
        r.setX(0.25)
        r.setY(0.25)
        b = QtGui.QLinearGradient(0, 0, 0, r.height())
        b.setColorAt(0, QtGui.QColor(0, 0, 0, 0))
        b.setColorAt(0.25, self.color)
        b.setColorAt(1, self.color)
        painter.setPen(QtCore.Qt.NoPen)
        b = QtGui.QBrush(self.bg)
        b.setStyle(QtCore.Qt.TexturePattern)
        painter.setBrush(b)
        painter.drawRoundedRect(r, self.roundCornerFactor, self.roundCornerFactor)
        # painter.setFont(self.descFont)
        parentRet = self.parentItem().childrenBoundingRect()
        if self.icon:
            painter.drawImage(QtCore.QRect(parentRet.width() - 9, 0, 8, 8), self.icon, QtCore.QRect(0, 0, self.icon.width(), self.icon.height()))

        painter.setClipping(True)
        if not self.clipRect:
            self.clipRect = QtCore.QRectF(0, 0, parentRet.width() - 5.0, self.boundingRect().height())
        painter.setClipRect(self.clipRect)
        # painter.setPen(self.descFontPen)
        # painter.drawText(5.0, self.h - 0.5, self.desc)

        super(NodeName, self).paint(painter, option, widget)

    def focusInEvent(self, event):
        self.scene().clearSelection()
        self.parentItem().graph().disable_sortcuts()


class Node(QGraphicsItem, NodeBase):
    """
    Default node description
    """
    def __init__(self, name, graph, w=120, color=Colors.NodeBackgrounds, spacings=Spacings, headColor=Colors.NodeNameRect):
        NodeBase.__init__(self, name, graph)
        QGraphicsItem.__init__(self)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.options = self.graph().get_settings()
        if self.options:
            self.opt_node_base_color = QtGui.QColor(self.options.value('NODES/Nodes base color'))
            self.opt_selected_pen_color = QtGui.QColor(self.options.value('NODES/Nodes selected pen color'))
            self.opt_lyt_a_color = QtGui.QColor(self.options.value('NODES/Nodes lyt A color'))
            self.opt_lyt_b_color = QtGui.QColor(self.options.value('NODES/Nodes lyt B color'))
            self.opt_pen_selected_type = QtCore.Qt.SolidLine
        self.object_type = ObjectTypes.Node
        self._left_stretch = 0
        self.color = color
        self.height_offset = 3
        self.spacings = spacings
        self.nodeMainGWidget = QGraphicsWidget()
        self._w = 0
        self.h = 40
        self.sizes = [0, 0, self.w, self.h, 1, 1]
        self.w = w
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsFocusable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.custom_widget_data = {}
        # node name
        self.label = weakref.ref(NodeName(self))
        # set node layouts
        self.nodeMainGWidget.setParentItem(self)
        # main
        self.portsMainLayout = QGraphicsLinearLayout(QtCore.Qt.Horizontal)
        self.portsMainLayout.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.portsMainLayout.setContentsMargins(1, 1, 1, 1)
        self.nodeMainGWidget.setLayout(self.portsMainLayout)
        self.nodeMainGWidget.setX(self.nodeMainGWidget.x())
        # inputs layout
        self.inputsLayout = QGraphicsLinearLayout(QtCore.Qt.Vertical)
        self.inputsLayout.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.inputsLayout.setContentsMargins(1, 1, 1, 1)
        self.portsMainLayout.addItem(self.inputsLayout)
        # outputs layout
        self.outputsLayout = QGraphicsLinearLayout(QtCore.Qt.Vertical)
        self.outputsLayout.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.outputsLayout.setContentsMargins(1, 1, 1, 1)
        self.portsMainLayout.addItem(self.outputsLayout)

        self.setZValue(1)
        self.setCursor(QtCore.Qt.OpenHandCursor)

        self.tweakPosition()
        self.icon = None

    @staticmethod
    def recreate(node):
        pos = node.scenePos()
        className = node.__class__.__name__
        name = node.name
        newNode = node.graph().create_node(className, pos.x(), pos.y(), name)
        node.kill()
        return newNode

    @property
    def w(self):
        return self._w

    @w.setter
    def w(self, value):
        self._w = value
        self.sizes[2] = value

    def call(self, name):
        if port_name in [p.name for p in self.outputs if p.data_type is DataTypes.Exec]:
            p = self.get_port_by_name(port_name)
            return p.call()

    def get_data(self, port_name):
        if port_name in [p.name for p in self.inputs]:
            p = self.get_port_by_name(port_name, PinSelectionGroup.Inputs)
            return p.get_data()

    def set_data(self, port_name, data):
        if port_name in [p.name for p in self.outputs]:
            p = self.get_port_by_name(port_name, PinSelectionGroup.Outputs)
            p.set_data(data)

    @staticmethod
    def initializeFromFunction(foo, graph):
        meta = foo.__annotations__['meta']
        returnType = foo.__annotations__['return']
        nodeType = foo.__annotations__['nodeType']
        doc = foo.__doc__

        @staticmethod
        def description():
            return doc

        @staticmethod
        def category():
            return meta['Category']

        @staticmethod
        def keywords():
            return meta['Keywords']

        def constructor(self, name, graph, **kwargs):
            Node.__init__(self, name, graph, **kwargs)

        nodeClass = type(foo.__name__, (Node,), {'__init__': constructor, 'category': category, 'keywords': keywords, 'description': description})
        inst = nodeClass(graph.get_uniq_node_name(foo.__name__), graph)

        if returnType is not None:
            inst.add_output_port('out', returnType)

        # this is array of 'references' outputs will be created for
        refs = []
        outExec = None

        # iterate over function arguments and create ports according to data types
        fooArgNames = getargspec(foo).args
        for index in range(len(fooArgNames)):
            dataType = foo.__annotations__[fooArgNames[index]]
            if dataType == DataTypes.Reference:
                outRef = inst.add_output_port(fooArgNames[index], foo.__defaults__[index])
                refs.append(outRef)
            else:
                inp = inst.add_input_port(fooArgNames[index], dataType)
                inp.set_data(foo.__defaults__[index])

        # all inputs affects on all outputs
        for i in inst.inputs:
            for o in inst.outputs:
                portAffects(i, o)

        # generate compute method from function
        def compute(self):
            # arguments will be taken from inputs
            kwargs = {}
            for i in self.inputs:
                if i.data_type is not DataTypes.Exec:
                    kwargs[i.name] = i.get_data()
            for ref in refs:
                if ref.data_type is not DataTypes.Exec:
                    kwargs[ref.name] = ref
            result = foo(**kwargs)
            if returnType is not None:
                self.set_data('out', result)
            if nodeType == NodeTypes.Callable:
                outExec.call()

        inst.compute = MethodType(compute, inst, Node)

        # create execs if callable
        if nodeType == NodeTypes.Callable:
            inst.add_input_port('inExec', DataTypes.Exec, inst.compute, True, index=0)
            outExec = inst.add_output_port('outExec', DataTypes.Exec, inst.compute, True, index=0)
        return inst

    def InputPinTypes(self):
        types = []
        for p in self.inputs:
            for t in p.supported_data_types:
                types.append(t)
        return types

    def tweakPosition(self):
        value = self.scenePos()
        self.setX(roundup(value.x() - self.graph().grid_size, self.graph().grid_size))
        self.setY(roundup(value.y() - self.graph().grid_size, self.graph().grid_size))

    def isCallable(self):
        for p in self.inputs + self.outputs:
            if p.data_type == DataTypes.Exec:
                return True
        return False

    def boundingRect(self):
        return self.childrenBoundingRect()

    def itemChange(self, change, value):
        if change == self.ItemPositionChange:
            # grid snapping
            value.setX(roundup(value.x() - self.graph().grid_size + self.graph().grid_size / 3.0, self.graph().grid_size))
            value.setY(roundup(value.y() - self.graph().grid_size + self.graph().grid_size / 3.0, self.graph().grid_size))
            value.setY(value.y() - 2)
            return value
        return QGraphicsItem.itemChange(self, change, value)

    @staticmethod
    def description():
        return "Default node description"

    def post_create(self):
        for i in range(0, self.inputsLayout.count()):
            container = self.inputsLayout.itemAt(i)
            lyt = container.layout()
            if lyt:
                for j in range(0, lyt.count()):
                    lyt.setAlignment(lyt.itemAt(j), QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)

        for i in range(0, self.outputsLayout.count()):
            container = self.outputsLayout.itemAt(i)
            lyt = container.layout()
            if lyt:
                for j in range(0, lyt.count()):
                    lyt.setAlignment(lyt.itemAt(j), QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
        self.w = self.getWidth()
        self.nodeMainGWidget.setMaximumWidth(self.w + self.spacings.kPortOffset)
        self.nodeMainGWidget.setGeometry(QtCore.QRectF(0, 0, self.w + self.spacings.kPortOffset, self.childrenBoundingRect().height()))
        if self.isCallable():
            if 'flow' not in self.category().lower():
                self.label().bg = QtGui.QImage(':/icons/resources/blue.png')
        else:
            self.label().bg = QtGui.QImage(':/icons/resources/green.png')
        self.label().setPlainText(self.__class__.__name__)
        self.setToolTip(self.description())

    def getWidth(self):
        dPorts = 0
        if len(self.outputs) > 0:
            dPorts = abs(self.outputs[0].scenePos().x() - self.scenePos().x())
        fontWidth = QtGui.QFontMetricsF(self.label().font()).width(self.get_name()) + self.spacings.kPortSpacing
        return max(dPorts, fontWidth)

    def save_command(self):
        return "createNode ~type {0} ~x {1} ~y {2} ~n {3}".format(self.__class__.__name__, self.scenePos().x(), self.scenePos().y(), self.name)

    def property_view(self):
        return self.graph().parent.dockWidgetNodeView

    def Tick(self, delta):
        pass

    def set_name(self, name):
        NodeBase.set_name(self, name)
        # self.label().setPlainText(self.name)

    def clone(self):
        pos = self.scenePos()
        name = self.graph().get_uniq_node_name(self.get_name())
        new_node = self.graph().create_node(self.__class__.__name__, pos.x(), pos.y(), name)
        return new_node

    def update_ports(self):
        [i.update() for i in self.inputs]
        [i.update() for i in self.outputs]

    def paint(self, painter, option, widget):

        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtCore.Qt.darkGray)

        if self.options:
            color = self.opt_node_base_color
        else:
            color = Colors.NodeBackgrounds
        if self.isSelected():
            color = color.lighter(150)

        linearGrad = QtGui.QRadialGradient(QtCore.QPointF(40, 40), 300)
        linearGrad.setColorAt(0, color)
        linearGrad.setColorAt(1, color.lighter(180))
        br = QtGui.QBrush(linearGrad)
        painter.setBrush(br)
        # painter.setOpacity(0.95)
        pen = QtGui.QPen(QtCore.Qt.black, 0.5)
        if option.state & QStyle.State_Selected:
            if self.options:
                pen.setColor(Colors.White)
                pen.setStyle(self.opt_pen_selected_type)
            else:
                pen.setColor(opt_selected_pen_color)
                pen.setStyle(self.opt_pen_selected_type)
        painter.setPen(pen)
        painter.drawRoundedRect(self.childrenBoundingRect(), self.sizes[4], self.sizes[5])

    def get_input_edges(self):
        out = {}
        for i in [i.edge_list for i in self.inputs]:
            if not i.__len__() == 0:
                out[i[0]] = [e.connection for e in i]
        return out

    def get_output_edges(self):
        out = {}
        for i in [i.edge_list for i in self.outputs]:
            if not i.__len__() == 0:
                out[i[0]] = [e.connection for e in i]
        return out

    def mousePressEvent(self, event):
        self.update()
        # self.setCursor(QtCore.Qt.ClosedHandCursor)
        QGraphicsItem.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        self.update()
        QGraphicsItem.mouseReleaseEvent(self, event)

    def add_input_port(self, port_name, data_type, foo=None, hideLabel=False, bCreateInputWidget=True, index=-1):
        p = self._add_port(PinTypes.Input, data_type, foo, hideLabel, bCreateInputWidget, port_name, index=index)
        return p

    @staticmethod
    def category():
        return "Default"

    @staticmethod
    def keywords():
        return []

    def add_output_port(self, port_name, data_type, foo=None, hideLabel=False, bCreateInputWidget=True, index=-1):
        p = self._add_port(PinTypes.Output, data_type, foo, hideLabel, bCreateInputWidget, port_name, index=index)
        return p

    def add_container(self, portType, head=False):
        container = QGraphicsWidget()  # for set background color
        container.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
        container.sizeHint(QtCore.Qt.MinimumSize, QtCore.QSizeF(50.0, 10.0))

        if self.graph().is_debug():
            container.setAutoFillBackground(True)
            container.setPalette(QtGui.QPalette(QtCore.Qt.gray))

        lyt = QGraphicsLinearLayout()
        lyt.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        lyt.setContentsMargins(1, 1, 1, 1)
        container.setLayout(lyt)
        if portType == PinTypes.Input:
            self.inputsLayout.addItem(container)
        else:
            self.outputsLayout.addItem(container)
        return container

    def kill(self):
        for i in self.inputs + self.outputs:
            i.disconnect_all()

        self.setVisible(False)
        self.graph().movePendingKill(self)

        self.graph().write_to_console("killNode {1}nl {0}".format(self.name, FLAG_SYMBOL))
        self.scene().removeItem(self)
        del(self)

    def set_pos(self, x, y):
        NodeBase.set_pos(self, x, y)
        self.setPos(QtCore.QPointF(x, y))

    def _add_port(self, port_type, data_type, foo, hideLabel=False, bCreateInputWidget=True, name='', color=QtGui.QColor(0, 100, 0, 255), index=-1):
        newColor = color

        if data_type == DataTypes.Int or DataTypes.Float:
            # set colot for numeric ports
            newColor = QtGui.QColor(0, 100, 0, 255)
        elif data_type == DataTypes.String:
            # set colot for string ports
            newColor = QtGui.QColor(50, 0, 50, 255)
        elif data_type == DataTypes.Bool:
            # set colot for bool ports
            newColor = QtGui.QColor(100, 0, 0, 255)
        elif data_type == DataTypes.Array:
            # set colot for bool ports
            newColor = QtGui.QColor(0, 0, 0, 255)
        else:
            newColor = QtGui.QColor(255, 255, 30, 255)

        p = Port(name, self, data_type, 7, 7, newColor)
        p.type = port_type
        if port_type == PinTypes.Input and foo is not None:
            p.call = foo
            # p.call = MethodType(foo, p, Port)
        connector_name = QGraphicsProxyWidget()
        connector_name.setContentsMargins(0, 0, 0, 0)

        lblName = name
        if hideLabel:
            lblName = ''
            p.bLabelHidden = True

        lbl = QLabel(lblName)
        lbl.setContentsMargins(0, 0, 0, 0)
        lbl.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        if self.options:
            font = QtGui.QFont(self.options.value('NODES/Port label font'))
            color = QtGui.QColor(self.options.value('NODES/Port label color'))
            font.setPointSize(int(self.options.value('NODES/Port label size')))
            lbl.setFont(font)
            style = 'color: rgb({0}, {1}, {2}, {3});'.format(
                color.red(),
                color.green(),
                color.blue(),
                color.alpha())
            lbl.setStyleSheet(style)
        connector_name.setWidget(lbl)
        if port_type == PinTypes.Input:
            container = self.add_container(port_type)
            if hideLabel:
                container.setMinimumWidth(15)
            lbl.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
            container.layout().addItem(p)
            p._container = container
            container.layout().addItem(connector_name)

            # create input widget
            if bCreateInputWidget:
                w = getPinWidget(p)
                if w:
                    container.layout().addItem(w.asProxy())

            self.inputs.append(p)
            self.inputsLayout.insertItem(index, container)
            container.adjustSize()
        elif port_type == PinTypes.Output:
            container = self.add_container(port_type)
            if hideLabel:
                container.setMinimumWidth(15)
            lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
            container.layout().addItem(connector_name)
            container.layout().addItem(p)
            p._container = container
            self.outputs.append(p)
            self.outputsLayout.insertItem(index, container)
            container.adjustSize()
        p.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        setattr(self, name, p)
        return p
