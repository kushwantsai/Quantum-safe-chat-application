import express from "express";
import { createServer } from "http";
import { Server } from "socket.io";
import axios from "axios";

const PORT = process.env.PORT || 8000;

const app = express();
const server = createServer(app);
const io = new Server(server, {
  cors: {
    origin: "*",
  },
});

const users = {};

io.on("connection", (socket) => {
  console.log("A user connected");

  socket.on("join", (username) => {
    console.log("joined", username);
    if (!username || users[username]) {
      socket.emit("join_error", "Username already taken");
    } else {
      users[username] = socket.id;
      io.emit("users_list", Object.keys(users)); // Send updated users list to all clients
    }
  });

  socket.on("disconnect", () => {
    const username = Object.keys(users).find((key) => users[key] === socket.id);
    if (username) {
      delete users[username];
      io.emit("user_left", username);
      io.emit("users_list", Object.keys(users)); // Send updated users list to all clients
    }
    console.log("A user disconnected");
  });

  socket.on("send_message", ({ sender, receiver, message }) => {
    console.log(sender, receiver, message, "socket");
    const receiverId = users[receiver];
    if (receiverId) {
      axios
        .post("http://172.20.10.12:9000/encrypt", { msg: message })
        .then(({ data }) => {
          console.log(message, data, "ópop");
          // Send message only to the intended recipient
          io.to(receiverId).emit("new_message", { sender, message: data });
        })
        .catch((e) => {
          console.log(e, "error");
        });
    } else {
      // Handle case where receiver is not found (e.g., user left the chat)
      io.emit("not_found", { message: `User ${receiver} not found.` });
      console.log(`User ${receiver} not found.`);
    }
  });
});

server.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
