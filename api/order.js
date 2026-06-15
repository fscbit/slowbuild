// Vercel Serverless Function — Order Notification
// Receives order form data, sends email notification via QQ SMTP

const nodemailer = require('nodemailer');

// QQ SMTP config
const SMTP = {
  host: 'smtp.qq.com',
  port: 465,
  secure: true,
  auth: {
    user: '184723392@qq.com',
    pass: 'tiabxxqucyhzbhbj'
  }
};

const NOTIFY_TO = '184723392@qq.com';

module.exports = async function handler(req, res) {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { product, price, name, email, address, notes } = req.body;

    if (!product || !name || !address) {
      return res.status(400).json({ error: 'Missing required fields: product, name, address' });
    }

    const orderId = 'SLW' + Date.now().toString(36).toUpperCase();
    const time = new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' });

    const html = `
      <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #e87d4b;">🛒 新订单通知</h2>
        <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
          <tr><td style="padding: 8px; border-bottom: 1px solid #eee; color: #666; width: 100px;">订单号</td><td style="padding: 8px; border-bottom: 1px solid #eee; font-weight: bold;">${orderId}</td></tr>
          <tr><td style="padding: 8px; border-bottom: 1px solid #eee; color: #666;">下单时间</td><td style="padding: 8px; border-bottom: 1px solid #eee;">${time}</td></tr>
          <tr><td style="padding: 8px; border-bottom: 1px solid #eee; color: #666;">商品</td><td style="padding: 8px; border-bottom: 1px solid #eee; font-size: 1.1em;">${product}</td></tr>
          <tr><td style="padding: 8px; border-bottom: 1px solid #eee; color: #666;">金额</td><td style="padding: 8px; border-bottom: 1px solid #eee; font-size: 1.2em; color: #e87d4b; font-weight: bold;">$${parseFloat(price).toFixed(2)}</td></tr>
          <tr><td style="padding: 8px; border-bottom: 1px solid #eee; color: #666;">买家</td><td style="padding: 8px; border-bottom: 1px solid #eee;">${name}</td></tr>
          <tr><td style="padding: 8px; border-bottom: 1px solid #eee; color: #666;">邮箱</td><td style="padding: 8px; border-bottom: 1px solid #eee;">${email || '(未填)'}</td></tr>
          <tr><td style="padding: 8px; border-bottom: 1px solid #eee; color: #666;">收货地址</td><td style="padding: 8px; border-bottom: 1px solid #eee; font-weight: bold;">${address}</td></tr>
          ${notes ? `<tr><td style="padding: 8px; border-bottom: 1px solid #eee; color: #666;">备注</td><td style="padding: 8px; border-bottom: 1px solid #eee;">${notes}</td></tr>` : ''}
        </table>
        <p style="color: #999; font-size: 12px; margin-top: 24px;">此邮件由 slowbuild.top 订单系统自动发送</p>
      </div>`;

    const transporter = nodemailer.createTransport(SMTP);
    await transporter.sendMail({
      from: `"slowbuild 订单" <184723392@qq.com>`,
      to: NOTIFY_TO,
      subject: `🛒 新订单 ${orderId} — ${product} $${parseFloat(price).toFixed(2)}`,
      html
    });

    res.status(200).json({ success: true, orderId });
  } catch (err) {
    console.error('Order API error:', err);
    res.status(500).json({ error: 'Failed to process order', detail: err.message });
  }
};
