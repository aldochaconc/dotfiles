import QtQuick
import QtQuick.Layouts
import Quickshell.Hyprland
import qs.Commons
import qs.Ui

BarWidget {
  id: root
  moduleName: "omarchy.workspaces"

  function workspaceById(id) {
    var values = Hyprland.workspaces.values
    for (var i = 0; i < values.length; i++) {
      if (values[i].id === id) return values[i]
    }

    return null
  }

  function workspaceIds() {
    var ids = [1, 2, 3, 4, 5]
    var values = Hyprland.workspaces.values

    for (var i = 0; i < values.length; i++) {
      var id = values[i].id
      if (id > 0 && id <= 10 && ids.indexOf(id) === -1) ids.push(id)
    }

    ids.sort(function(left, right) { return left - right })
    return ids
  }

  function focusWorkspace(id) {
    if (!root.bar) return
    root.bar.run("hyprctl dispatch " + Util.shellQuote("hl.dsp.focus({ workspace = \"" + id + "\" })"))
  }

  // Rotation is delegated to hypr-workspace-rotate rather than computed here, so the
  // ceiling (1..5, plus higher workspaces while occupied) has one implementation instead
  // of a second copy in QML that could drift from workspaceIds() above.
  //
  // A touchpad delivers many small deltas per gesture where a wheel sends one notch, so
  // an unthrottled handler would fire the script dozens of times per scroll. The cooldown
  // collapses a burst into one step.
  property bool rotating: false

  Timer {
    id: rotateCooldown
    interval: 120
    onTriggered: root.rotating = false
  }

  function rotate(direction) {
    if (!root.bar || root.rotating) return
    root.rotating = true
    rotateCooldown.restart()
    // run goes through bash -lc, a login shell, so ~/.local/bin is on PATH.
    root.bar.run("hypr-workspace-rotate " + direction)
  }

  readonly property real trailingGap: root.vertical ? 0 : Style.spaceReal(1.5)

  implicitWidth: grid.implicitWidth + trailingGap
  implicitHeight: grid.implicitHeight

  // The focused indicator changed colour in place, so a swipe gave no cue for which
  // direction it moved. One rectangle tracks the focused button's own geometry instead:
  // the eye follows a single object travelling, which reads as direction where a
  // simultaneous fade on two separate buttons does not.
  //
  // Geometry is read off the button rather than recomputed from index and spacing, so
  // spacing scale, the vertical bar and the variable workspace count stay in one place.
  Rectangle {
    id: pill
    property Item target: null

    color: Color.bar.active
    opacity: 0.18
    radius: Style.cornerRadius
    visible: target !== null
    z: -1

    x: target ? target.x : 0
    y: target ? target.y : 0
    width: target ? target.width : 0
    height: target ? target.height : 0

    // OutCubic is what the shell already uses for a sliding element (Ui/PanelSlider.qml,
    // Ui/WidgetButton.qml's own opacity Behavior), at 140. 120 here instead, matching
    // rotateCooldown above: the pill finishes exactly as the next swipe step unlocks.
    //
    // The jump from no target to a target is a first paint, not a move, so animating it
    // would slide the pill in from the corner on startup. Enabling the Behaviors only
    // once a target exists keeps that first placement instant.
    Behavior on x { enabled: pill.target !== null; NumberAnimation { duration: 120; easing.type: Easing.OutCubic } }
    Behavior on y { enabled: pill.target !== null; NumberAnimation { duration: 120; easing.type: Easing.OutCubic } }
    Behavior on width { enabled: pill.target !== null; NumberAnimation { duration: 120; easing.type: Easing.OutCubic } }
    Behavior on height { enabled: pill.target !== null; NumberAnimation { duration: 120; easing.type: Easing.OutCubic } }
  }

  GridLayout {
    id: grid
    anchors.fill: parent
    anchors.rightMargin: root.trailingGap
    columns: root.vertical ? 1 : root.workspaceIds().length
    columnSpacing: root.vertical ? 0 : Style.space(1)
    rowSpacing: root.vertical ? Style.space(2) : 0

    Repeater {
      model: root.workspaceIds()

      WidgetButton {
        required property int modelData

        readonly property var workspace: root.workspaceById(modelData)
        readonly property bool occupied: workspace !== null && workspace.toplevels.values.length > 0
        readonly property bool focused: Hyprland.focusedWorkspace !== null && Hyprland.focusedWorkspace.id === modelData

        bar: root.bar
        text: focused ? "\uDB85\uDCFB" : (modelData === 10 ? "0" : String(modelData))
        opacity: occupied || focused ? 1 : 0.5
        horizontalMargin: 6
        verticalPadding: 6
        fixedWidth: root.vertical ? root.barSize : Style.space(20)
        fixedHeight: root.barSize
        onPressed: function() { root.focusWorkspace(modelData) }

        // The focused button claims the pill. Binding from here rather than searching
        // the Repeater for the focused index keeps it to one line and survives the
        // model changing when a higher workspace opens or closes.
        onFocusedChanged: if (focused) pill.target = this
        Component.onCompleted: if (focused) pill.target = this

        // Scroll over any workspace indicator rotates workspaces, the same move as the
        // 3-finger swipe and SUPER + scroll. wheelMoved is WidgetButton's own signal,
        // the same hook omarchy.microphone and omarchy.audio use for their scroll.
        onWheelMoved: function(delta) { root.rotate(delta > 0 ? "next" : "prev") }
      }
    }
  }
}
