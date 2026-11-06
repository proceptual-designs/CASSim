import 'package:flet/flet.dart';
import 'package:flutter/widgets.dart';

import 'flet_ping.dart';

class Extension extends FletExtension {
  @override
  Widget? createWidget(Key? key, Control control) {
    switch (control.type) {
      case "FletPing":
        return FletPingControl(control: control);
      default:
        return null;
    }
  }
}
