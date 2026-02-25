import pathlib

path = pathlib.Path(r"c:\Users\слава\Documents\GitHub\пивоо\app.py")
lines = path.read_text(encoding='utf-8').splitlines()
new_lines = []
found = False
for line in lines:
    new_lines.append(line)
    if line.strip() == "return app" and not found:
        found = True
        break
if not found:
    print("First return app not found")
else:
    out = new_lines + ["", "if __name__ == '__main__':", "    app = create_app()", "    app.run(debug=True, host='0.0.0.0', port=5000)"]
    path.write_text("\n".join(out), encoding='utf-8')
    print("Truncated file and added run block")
