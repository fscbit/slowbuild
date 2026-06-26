with open(r'C:\Users\方世聪\.cloudflared\config.yml', 'w', encoding='utf-8') as f:
    f.write("""tunnel: 31912a21-8981-455d-8df9-adc4a2cce071
credentials-file: C:/Users/方世聪/.cloudflared/31912a21-8981-455d-8df9-adc4a2cce071.json

ingress:
  - hostname: api.slowbuild.top
    service: http://localhost:5000
  - hostname: order.slowbuild.top
    service: http://localhost:5001
  - service: http_status:404
""")
print("config.yml OK")
