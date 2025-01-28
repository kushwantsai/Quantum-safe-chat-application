import { useState, useEffect } from 'react';
import { Button, TextField, Typography, Container, styled } from '@mui/material';
import { toast } from 'react-toastify';
import ChatPage from './main-chat';
import { io } from 'socket.io-client';


const StyledContainer = styled(Container)(({ theme }) => ({
	marginTop: theme.spacing(4),
	display: 'flex',
	flexDirection: 'column',
	alignItems: 'center',
}));

const StyledForm = styled('form')(({ theme }) => ({
	width: '100%',
	marginTop: theme.spacing(1),
}));

const StyledButton = styled(Button)(({ theme }) => ({
	margin: theme.spacing(3, 0, 2),
}));

const url = 'http://localhost:8000';

const ChatApp = () => {

	const [socket, setSocket] = useState();
	const [username, setUsername] = useState('');
	const [joined, setJoined] = useState(false); // Track whether user has joined
	const [usersList, setUsersList] = useState([]);

	useEffect(() => {
		if (socket) {
			socket.on('users_list', (users) => {
				setUsersList(users);
			});
		}
	}, [socket]);

	useEffect(() => {
		const socketInstance = io(url);
		setSocket(socketInstance);
		if (joined) {
			setJoined((joined) => !joined)
		}

		return () => {
			socketInstance.disconnect();
		};
	}, []);


	const handleUsernameChange = (event) => {
		setUsername(event.target.value);
	};

	const handleJoinChat = () => {
		if (username.trim() === '') {
			toast.error('Please enter a valid username!');
		} else {
			if (socket) {
				socket.emit('join', username);
				setJoined(true); // Set joined to true upon successful join
			} else {
				toast.error('Failed to connect to the chat server!');
			}
		}
	};

	return (
		<StyledContainer component="main" maxWidth="lg">
			{!joined ? (
				<>
					<Typography variant="h5">Welcome to the Chat App</Typography>
					<StyledForm noValidate>
						<TextField
							variant="outlined"
							margin="normal"
							required
							fullWidth
							id="username"
							label="Enter Your Name"
							name="username"
							value={username}
							onChange={handleUsernameChange}
						/>
						<StyledButton
							type="button"
							fullWidth
							variant="contained"
							color="primary"
							onClick={handleJoinChat}
						>
							Join Chat
						</StyledButton>
					</StyledForm>
				</>
			) : (
				<ChatPage usersList={usersList} socket={socket} username={username} />
			)}
		</StyledContainer>
	);
};

export default ChatApp;
