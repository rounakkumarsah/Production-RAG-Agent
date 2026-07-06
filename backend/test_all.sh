for ext in pdf docx pptx xlsx csv txt md; do
  echo "Testing $ext"
  curl -s -X POST -F "files=@/tmp/test.$ext" http://localhost:8000/upload
  echo ""
done
