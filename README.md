# Browser Copilot Live Safe v0.2

รุ่นนี้อัปเกรดจาก localhost-only เป็น live-tab read mode ด้วยสิทธิ์น้อยที่สุด

## ติดตั้ง
1. แตก ZIP
2. เปิด `chrome://extensions`
3. เปิด Developer mode
4. กด Load unpacked แล้วเลือกโฟลเดอร์นี้
5. กดไอคอนส่วนขยายเพื่อเปิด Side Panel
6. เพิ่มโดเมนที่อนุญาต เช่น `google.com` หรือ `github.com`
7. เปิดแท็บนั้น แล้วกด "อ่านและวิเคราะห์แท็บ"

## ความปลอดภัย
- ใช้ `activeTab` + `scripting`: ได้สิทธิ์ชั่วคราวเมื่อผู้ใช้เรียกใช้ส่วนขยาย ไม่ขอ host permission ทั้งเว็บ
- ไม่มี anti-detect, stealth, proxy rotation, CAPTCHA solver หรือการหลบระบบตรวจจับ
- ไม่อ่านค่า input/password/cookie และไม่ส่งข้อมูลไปบริการภายนอก
- ตรวจข้อความที่อาจเป็น prompt injection และแยกเว็บเป็น untrusted data
- มีโหมด Observe/Guide/Approve/Auto-Safe และ audit log ในเครื่อง
- Auto-Safe ยังจำกัดไว้สำหรับ sandbox/localhost; action เสี่ยงยังไม่ถูกทำอัตโนมัติ

## Action Policy Engine
คำสั่งจะถูกจำแนกเป็น `allowed` (อ่าน/ตรวจ/รัน test ที่จำกัด), `approval_required` (คลิก กรอก อัปโหลด แก้ patch ส่งฟอร์ม เผยแพร่) หรือ `blocked` (รหัสผ่าน คุกกี้ การเงิน พนัน CAPTCHA และการหลบระบบ). คำสั่งที่ไม่รู้จักจะ default เป็น approval_required.

## Safe Executor
มี `/execute` สำหรับ `run_tests` และ `read_project_file` แบบจำกัดเส้นทางเท่านั้น. Action ที่มีผลข้างเคียงจะหยุดรอ approval และไม่มี executor ให้รันใน Safe MVP; action ที่เสี่ยงจะถูกบล็อก. ทุก execution ถูกบันทึกใน `audit.jsonl`.

## Local Operator
รัน `./run-local-agent.sh` เพื่อเปิด backend ที่ `http://127.0.0.1:8787` จากนั้นกด "วิเคราะห์ผ่าน Local Operator" ใน Side Panel. Backend นี้ทำ redaction, ตรวจ prompt injection, จัดระดับความเสี่ยง และสร้างแผนเท่านั้น — ไม่มี browser control และไม่มีการส่งข้อมูลออกนอกเครื่อง. หาก backend ไม่ทำงาน ส่วนขยายจะยังอ่านและวิเคราะห์แบบ local ได้.

## ข้อจำกัด
รุ่นนี้มี analyzer แบบ local เพื่อยืนยันเส้นทางการทำงาน ยังไม่ได้เชื่อม LLM backend จริง การเชื่อม LLM ควรทำผ่าน backend ที่มี policy, redaction, rate limit, audit log และ human approval ก่อน action เสี่ยง
