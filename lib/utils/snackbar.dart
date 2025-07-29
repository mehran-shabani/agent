import 'package:flutter/material.dart';

class CustomSnackBar {
  static void show(String message, BuildContext context, {bool isError = false}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: isError ? Colors.red : Colors.green,
      ),
    );
  }
}
