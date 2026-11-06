import 'package:flet/flet.dart';
import 'package:flutter/material.dart';

class FletPingControl extends StatelessWidget {
  final Control control;

  const FletPingControl({super.key, required this.control});

  @override
  Widget build(BuildContext context) {
    String text = control.getString("value", "")!;
    // A tap sends an event from Dart to Python (the path a MathLive/key-handler control would use).
    Widget myControl = GestureDetector(
      onTap: () => control.triggerEvent("ping", {"from": "dart"}),
      child: Container(
        color: Colors.deepPurple,
        padding: const EdgeInsets.all(24),
        child: Text(text, style: const TextStyle(color: Colors.white, fontSize: 24)),
      ),
    );
    return LayoutControl(control: control, child: myControl);
  }
}
