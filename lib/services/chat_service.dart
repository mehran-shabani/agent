// lib/services/chat_service.dart
// A single façade that the UI talks to. It hides token-handling via
// shared_preferences, builds the MedAgent-backend requests, and knows
// how to format a Gemini-Vision message when the user attaches a
// medical image.

import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:mime/mime.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Your Django-backend root (e.g. https://med.example.com)
const String backendBase = '<BACKEND_BASE_URL_HERE>'; // keep ⬅️  remember to fill in!

/// Convenience wrapper around SharedPreferences so we always have the latest
Future<SharedPreferences> get _prefs async => SharedPreferences.getInstance();

class ChatService {
  static const _hdrJson = {'Content-Type': 'application/json; charset=utf-8'};

  //--------------------------------------------------------------------------
  //  TOKEN HELPERS
  //--------------------------------------------------------------------------
  Future<String?> _readToken() async => (await _prefs).getString('access');

  Future<Map<String, String>> _authorizedHeaders() async {
    final token = await _readToken();
    if (token == null) throw Exception('No access token available');
    return {
      ..._hdrJson,
      'Authorization': 'Bearer $token',
    };
  }

  //--------------------------------------------------------------------------
  //  HIGH-LEVEL API SURFACE
  //--------------------------------------------------------------------------

  /// GET /api/patient/profile/ – returns a (possibly null) JSON map.
  Future<Map<String, dynamic>?> getMedicalProfile() async {
    final r = await http.get(
      Uri.parse('$backendBase/api/patient/profile/'),
      headers: await _authorizedHeaders(),
    );
    if (r.statusCode == 200) return jsonDecode(r.body) as Map<String, dynamic>;
    return null;
  }

  /// GET /api/session/{sessionId}/history/
  Future<List<Map<String, dynamic>>> getChatHistory({String? sessionId}) async {
    final url = sessionId == null
        ? '$backendBase/api/session/history/'
        : '$backendBase/api/session/$sessionId/history/';
    final r = await http.get(Uri.parse(url), headers: await _authorizedHeaders());
    if (r.statusCode == 200) {
      final list = jsonDecode(r.body) as List;
      return list.cast<Map<String, dynamic>>();
    }
    return [];
  }

  /// POST /api/session/create/
  Future<Map<String, dynamic>> createNewSession({
    required String sessionType, // forwarded as `purpose` on backend
    int? patientId,
  }) async {
    final body = {
      if (patientId != null) 'patient_id': patientId,
      'purpose': sessionType,
    };
    final r = await http.post(
      Uri.parse('$backendBase/api/session/create/'),
      headers: await _authorizedHeaders(),
      body: jsonEncode(body),
    );
    if (r.statusCode == 201) {
      return jsonDecode(r.body) as Map<String, dynamic>;
    }
    throw HttpException('Create session failed (${r.statusCode})');
  }

  /// POST /api/session/{sessionId}/message/
  Future<Map<String, dynamic>> sendMessage({
    required int sessionId,
    required String message,
  }) async {
    final r = await http.post(
      Uri.parse('$backendBase/api/session/$sessionId/message/'),
      headers: await _authorizedHeaders(),
      body: jsonEncode({'session': sessionId, 'content': message}),
    );
    if (r.statusCode == 200) {
      return jsonDecode(r.body) as Map<String, dynamic>;
    }
    throw HttpException('Send message failed (${r.statusCode})');
  }

  /// PATCH /api/session/end/
  Future<bool> endSession(int sessionId) async {
    final r = await http.patch(
      Uri.parse('$backendBase/api/session/end/'),
      headers: await _authorizedHeaders(),
      body: jsonEncode({'session_id': sessionId}),
    );
    return r.statusCode == 200;
  }

  //--------------------------------------------------------------------------
  //  MEDICAL IMAGE ANALYSIS (GPT-4 V / Gemini Vision)
  //--------------------------------------------------------------------------
  /// Sends a local image + (optional) user caption for analysis.
  ///
  /// The MedAgent backend exposes /analysis/vision that will forward the
  /// request to TalkBot’s /v1/chat/completions with the proper format.
  /// We therefore post a JSON payload that already contains the array of
  /// messages expected by GPT-4 Vision / Gemini-Pro Vision.
  Future<Map<String, dynamic>> analyzeImage({
    required File imageFile,
    String caption = '',
    String model = 'gemini-pro-vision',
  }) async {
    final bytes = await imageFile.readAsBytes();
    final b64 = base64Encode(bytes);
    final mime = lookupMimeType(imageFile.path) ?? 'image/jpeg';

    final imageDataUri = 'data:$mime;base64,$b64';

    final messages = [
      {
        'role': 'user',
        'content': [
          {
            'type': 'image_url',
            'image_url': {'url': imageDataUri},
          },
          {
            'type': 'text',
            'text': caption.isEmpty ? 'Analyse this medical image' : caption,
          },
        ],
      },
    ];

    // 1️⃣  Hit MedAgent backend – it will relay the request to TalkBot.
    final r = await http.post(
      Uri.parse('$backendBase/analysis/vision'),
      headers: await _authorizedHeaders(),
      body: jsonEncode({
        'model': model,
        'messages': messages,
        'temperature': 0.7,
        'stream': false,
        'top_p': 1.0,
      }),
    );

    if (r.statusCode == 200) {
      return jsonDecode(r.body) as Map<String, dynamic>;
    }
    throw HttpException('Image analysis failed (${r.statusCode})');
  }
}
