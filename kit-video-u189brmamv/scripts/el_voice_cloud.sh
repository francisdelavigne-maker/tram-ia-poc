#!/bin/bash
# Voix off (7 scènes), voix Liam. Environnement cloud : la clé ElevenLabs est ajoutée par l'environnement (secret réseau), ne PAS envoyer d'en-tête de clé.
# Usage: el_voice_cloud.sh <script.json> <dossier_sortie>
SCRIPT="$1"; OUT="$2"; mkdir -p "$OUT"
VOICE="TX3LPaxmHKxFdv7VOQHJ"
for s in s1 s2 s3 s4 s5 s6 s7; do
  BODY=$(python3 -I -c '
import json,sys
S=json.load(open(sys.argv[2]))
k=sys.argv[1]; ks=list(S); i=ks.index(k)
d={"text":S[k],"model_id":"eleven_multilingual_v2","voice_settings":{"stability":0.4,"similarity_boost":0.8,"style":0.45,"use_speaker_boost":True}}
if i>0: d["previous_text"]=S[ks[i-1]][-200:]
if i<len(ks)-1: d["next_text"]=S[ks[i+1]][:200]
print(json.dumps(d))' "$s" "$SCRIPT")
  curl -s -o "$OUT/$s.mp3" -w "$s HTTP %{http_code} %{size_download} octets\n" \
    -X POST "https://api.elevenlabs.io/v1/text-to-speech/$VOICE?output_format=mp3_44100_128" \
    -H "Content-Type: application/json" -d "$BODY"
done
