/* eslint-disable react/prop-types */
import { useEffect, useState } from "react";
import { toast } from "react-toastify";
import {
  Grid,
  Typography,
  Button,
  Paper,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Stack,
  Box,
  CircularProgress,
} from "@mui/material";
import axios from "axios";

const ChatPage = ({ usersList, socket, username }) => {
  const [selectedUser, setSelectedUser] = useState("");
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    if (socket) {
      const handleNewMessage = (data) => {
        setMessages((prevMessages) => [...prevMessages, data]);
      };

      const notFound = (data) => {
        toast.info(data.message);
      };

      socket.on("new_message", handleNewMessage);
      socket.on("not_found", notFound);

      // Clean up previous event listener
      return () => {
        socket.off("new_message", handleNewMessage);
        socket.off("not_found", notFound);
      };
    }
  }, [socket]);

  const handleMessageChange = (event) => {
    setMessage(event.target.value);
  };

  const handleSendMessage = () => {
    if (message.trim() === "") {
      toast.error("Please enter a message!");
    } else if (!selectedUser) {
      toast.error("Please select a user to send the message!");
    } else {
      const sender = username;
      socket.emit("send_message", { sender, receiver: selectedUser, message });
      setMessages([...messages, { sender, message }]);
      setMessage("");
    }
  };

  const handleUserSelect = (user) => {
    setSelectedUser(user);
    toast.success(`Selected user: ${user}`);
  };

  return (
    <Grid container spacing={2}>
      <Grid item xs={4}>
        <Typography variant="subtitle1" color="primary">
          Logged In {username}
        </Typography>
        <List component={Paper} dense sx={{ p: 2, minHeight: 600, height: "100%", backgroundColor: "#f4e5ff" }}>
          <Typography variant="subtitle2">Joined Users</Typography>
          {usersList
            .filter((user) => user !== username)
            .map((user) => (
              <ListItem sx={{ borderBottom: "1px solid", borderColor: "divider" }} disablePadding key={user}>
                <ListItemButton selected={user === selectedUser} onClick={() => handleUserSelect(user)}>
                  <ListItemText primary={user} />
                </ListItemButton>
              </ListItem>
            ))}
        </List>
      </Grid>
      <Grid item xs={8}>
        {/* Right side: Message content */}
        <Typography variant="subtitle1" color="secondary">
          Send Message to {selectedUser}
        </Typography>
        <Stack
          component={Paper}
          style={{ overflowY: "auto", padding: "8px", minHeight: 600, height: "100%", backgroundColor: "#f4e5ff" }}
        >
          <Stack sx={{ flex: 1, marginTop: "auto" }}>
            {messages.map((msg, index) => (
              <MessageBubble
                index={index}
                msg={msg}
                username={username}
                key={index}
                setMessages={setMessages}
                messages={messages}
              />
            ))}
          </Stack>
          <Stack borderRadius={1} direction="row" alignItems="center" border="1px solid" borderColor="divider">
            <input
              style={{
                appearance: "none",
                paddingInline: 16,
                paddingBlock: 8,
                border: "none",
                outline: "none",
                flex: 1,
              }}
              id="message"
              name="message"
              value={message}
              onChange={handleMessageChange}
              onKeyDown={(e) => {
                if (e.code === "Enter") {
                  handleSendMessage();
                }
              }}
            />
            {/* Send message button */}
            <Button type="button" variant="outlined" color="primary" onClick={handleSendMessage}>
              Send
            </Button>
          </Stack>
        </Stack>
        {/* Message input field */}
      </Grid>
    </Grid>
  );
};

export default ChatPage;

function MessageBubble({ msg, username, setMessages }) {
  const [loading, setLoading] = useState(false);
  const [disabled, setDisabled] = useState(false);

  function decrypt_msg(msg) {
    setLoading(true);
    axios
      .post("http://172.20.10.12:9000/decrypt", { msg: msg.message })
      .then(({ data }) => {
        setMessages((prevMessages) => {
          const msgs = [];
          prevMessages.forEach((m) => {
            if (m.sender == msg.sender && m.message === msg.message) {
              msgs.push({ ...m, message: data });
            } else {
              msgs.push(m);
            }
          });
          return msgs;
        });
        setLoading(false);
        setDisabled(true);
      })
      .catch((e) => {
        console.log(e);
        setLoading(false);
      });
  }

  if (username !== msg.sender) {
    return (
      <Box sx={{ marginBlock: 1 }}>
        <Stack sx={{ flexDirection: "row", alignItems: "flex-end" }}>
          <Typography
            align="center"
            variant="subtitle1"
            sx={{
              backgroundColor: "#505872",
              color: "white",
              mr: 1,
              minWidth: 50,
              border: "1px solid",
              borderColor: "divider",
              borderRadius: 3,
              borderBottomRightRadius: 0,
            }}
          >
            {msg.sender}
          </Typography>
          <Typography
            variant="body1"
            sx={{
              minWidth: 300,
              backgroundColor: "#eee",
              border: "1px solid",
              borderColor: "divider",
              borderRadius: 2,
              borderBottomLeftRadius: 0,
              px: 2,
              py: 1,
            }}
          >
            {msg.message}
            {loading && <CircularProgress size={20} />}

            <Button disabled={disabled || loading} onClick={() => decrypt_msg(msg)}>
              Decrypt
            </Button>
          </Typography>
        </Stack>
      </Box>
    );
  }

  return (
    <Box sx={{ marginBlock: 1 }}>
      <Stack sx={{ flexDirection: "row", alignItems: "flex-end", justifyContent: "right" }}>
        <Typography
          variant="body1"
          sx={{
            minWidth: 300,
            backgroundColor: "aliceblue",
            border: "1px solid",
            borderColor: "divider",
            borderRadius: 2,
            borderBottomRightRadius: 0,
            px: 2,
            py: 1,
          }}
        >
          {msg.message}
        </Typography>
        <Typography
          align="center"
          variant="subtitle1"
          sx={{
            backgroundColor: "#505872",
            color: "white",
            ml: 1,
            minWidth: 50,
            border: "1px solid",
            borderColor: "divider",
            borderRadius: 3,
            borderBottomLeftRadius: 0,
          }}
        >
          {msg.sender}
        </Typography>
      </Stack>
    </Box>
  );
}
