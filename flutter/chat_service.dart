import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ChatService {
  static const String baseUrl = 'http://localhost:8000';

  Future<String?> _token() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('access_token');
  }

  Future<int?> createSession() async {
    final token = await _token();
    final res = await http.post(
      Uri.parse('$baseUrl/api/session/create/'),
      headers: {'Authorization': 'Bearer $token'},
    );
    if (res.statusCode == 201) {
      return jsonDecode(res.body)['session_id'] as int;
    }
    return null;
  }

  Future<String?> sendMessage(int sessionId, String text) async {
    final token = await _token();
    final res = await http.post(
      Uri.parse('$baseUrl/api/session/$sessionId/message/'),
      headers: {'Authorization': 'Bearer $token'},
      body: {'content': text},
    );
    if (res.statusCode == 200) {
      return jsonDecode(res.body)['assistant_reply'] as String;
    }
    return null;
  }

  Future<void> endSession(int sessionId) async {
    final token = await _token();
    await http.patch(
      Uri.parse('$baseUrl/api/session/end/'),
      headers: {'Authorization': 'Bearer $token'},
      body: {'session_id': '$sessionId'},
    );
  }
}
