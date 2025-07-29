import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ChatService {
  ChatService({required this.baseUrl});

  final String baseUrl;

  Future<String?> _token() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('access_token') ?? prefs.getString('access');
  }

  Future<Map<String, String>> _headers({bool jsonBody = true}) async {
    final token = await _token();
    return {
      if (jsonBody) 'Content-Type': 'application/json',
      if (token != null && token.isNotEmpty) 'Authorization': 'Bearer $token',
    };
  }

  Uri _url(String path) => Uri.parse('$baseUrl$path');

  http.Client get _client => http.Client();

  // Auth & OTP
  Future<void> requestOtp(String nationalCode) async {
    final resp = await _client.post(
      _url('/api/otp/request/'),
      headers: await _headers(),
      body: jsonEncode({'national_code': nationalCode}),
    );
    if (resp.statusCode != 200) {
      throw HttpException('OTP request failed (${resp.statusCode})');
    }
  }

  Future<String> verifyOtp({required String nationalCode, required String code}) async {
    final resp = await _client.post(
      _url('/api/otp/verify/'),
      headers: await _headers(),
      body: jsonEncode({'national_code': nationalCode, 'code': code}),
    );
    if (resp.statusCode != 200) {
      throw HttpException('OTP verify failed (${resp.statusCode})');
    }
    final data = jsonDecode(resp.body) as Map<String, dynamic>;
    final token = data['access'] as String;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('access_token', token);
    return token;
  }

  // Chat session
  Future<int> createSession(int patientId, {String? purpose}) async {
    final resp = await _client.post(
      _url('/api/session/create/'),
      headers: await _headers(),
      body: jsonEncode({'patient_id': patientId, if (purpose != null) 'purpose': purpose}),
    );
    if (resp.statusCode != 201) {
      throw HttpException('Create session failed (${resp.statusCode})');
    }
    return (jsonDecode(resp.body) as Map<String, dynamic>)['session_id'] as int;
  }

  Future<String> sendMessage({required int sessionId, required String content}) async {
    final resp = await _client.post(
      _url('/api/session/$sessionId/message/'),
      headers: await _headers(),
      body: jsonEncode({'session': sessionId, 'content': content}),
    );
    if (resp.statusCode != 200) {
      throw HttpException('Send message failed (${resp.statusCode})');
    }
    return (jsonDecode(resp.body) as Map<String, dynamic>)['assistant_reply'] as String;
  }

  Future<void> endSession(int sessionId) async {
    final resp = await _client.patch(
      _url('/api/session/end/'),
      headers: await _headers(),
      body: jsonEncode({'session_id': sessionId}),
    );
    if (resp.statusCode != 200) {
      throw HttpException('End session failed (${resp.statusCode})');
    }
  }

  // Image analysis
  Future<Map<String, dynamic>> analyzeImage(String base64) async {
    final resp = await _client.post(
      _url('/api/tools/analyze_image/'),
      headers: await _headers(),
      body: jsonEncode({'b64': base64}),
    );
    if (resp.statusCode != 200) {
      throw HttpException('Analyze image failed (${resp.statusCode})');
    }
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  // Session management
  Future<bool> isSessionActive(int sessionId) async {
    try {
      final resp = await _client.get(
        _url('/api/session/$sessionId/status/'),
        headers: await _headers(jsonBody: false),
      );
      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body) as Map<String, dynamic>;
        return data['is_active'] as bool;
      }
      return false;
    } catch (e) {
      return false;
    }
  }

  // Auto-close session after timeout
  Future<void> autoCloseSession(int sessionId) async {
    try {
      await endSession(sessionId);
    } catch (e) {
      // Session already closed or error
    }
  }
}
