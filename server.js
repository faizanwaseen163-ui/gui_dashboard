const express = require("express");
const http = require("http");
const path = require("path");
const os = require("os");

const app = express();
const PORT = 3000;
const PY_API = "http://127.0.0.1:3002/api";

app.use(express.static(__dirname));

app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "index.html"));
});

app.get("/network", (req, res) => {
  const nets = os.networkInterfaces();
  let ip = "127.0.0.1";
  for (const name of Object.keys(nets)) {
    for (const net of nets[name]) {
      if (net.family === "IPv4" && !net.internal) {
        ip = net.address;
        break;
      }
    }
    if (ip !== "127.0.0.1") break;
  }
  res.json({ ip, port: PORT, url: `http://${ip}:${PORT}` });
});

app.get("/stream", (req, res) => {
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache, no-transform");
  res.setHeader("Connection", "keep-alive");
  res.setHeader("X-Accel-Buffering", "no");
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.flushHeaders();

  const tick = () => {
    http.get(PY_API, (pyRes) => {
      let raw = "";
      pyRes.on("data", (chunk) => (raw += chunk));
      pyRes.on("end", () => {
        try {
          JSON.parse(raw);
          res.write(`data: ${raw}\n\n`);
          if (typeof res.flush === "function") res.flush();
        } catch (e) {
          res.write(`event: error\ndata: {"error":"bad json"}\n\n`);
        }
      });
    }).on("error", () => {
      res.write(`event: error\ndata: {"error":"python api unreachable"}\n\n`);
    });
  };

  tick();
  const id = setInterval(tick, 1000);
  req.on("close", () => clearInterval(id));
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(`\n  ✅ Web Dashboard running`);
  console.log(`     Local:   http://localhost:${PORT}`);
  console.log(`     Network: http://<your-ip>:${PORT}\n`);
});