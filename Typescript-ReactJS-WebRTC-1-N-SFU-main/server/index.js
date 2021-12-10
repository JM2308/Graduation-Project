let http = require("http");
let express = require("express");
let cors = require("cors");
let socketio = require("socket.io");
let wrtc = require("wrtc");

const app = express();
const server = http.createServer(app);

app.use(cors());

let receiverPCs = {}; // 접속한 user의 MediaStream을 받기 위한 RTCPeerConnection을 저장
let senderPCs = {}; // 한 user에게 자신을 제외한 다른 user의 MediaStream을 보내기 위한 RTCPeerConnection을 저장
let users = {}; // receivePCs에서 연결된 RTCPeerConnection을 통해 받은 MediaStream을 user의 socketID와 함께 저장 (MediaStream과 socketID 저장)
let socketToRoom = {}; // user가 어떤 room에 속해 있는지 저장

const pc_config = {
  iceServers: [
    // {
    //   urls: 'stun:[STUN_IP]:[PORT]',
    //   'credentials': '[YOR CREDENTIALS]',
    //   'username': '[USERNAME]'
    // },
    {
      urls: "stun:stun.l.google.com:19302",
    },
  ],
};

const isIncluded = (array, id) => array.some((item) => item.id === id); // 배열 내의 Dictionary 중 id가 일치하는 것이 존재하는지 여부 반환

const createReceiverPeerConnection = (socketID, socket, roomID) => { // (string, socketio.Socket, string)
  // user의 socketID를 key로 한 receiverPCs의 value로, 새로 생성한 pc를 저장하고, 그 pc를 통해 user의 MediaStream을 전달받는 이벤트 생성
  const pc = new wrtc.RTCPeerConnection(pc_config);

  if (receiverPCs[socketID]) receiverPCs[socketID] = pc; // RTCPeerConnection 변수
  else receiverPCs = { ...receiverPCs, [socketID]: pc };

  pc.onicecandidate = (e) => {
    //console.log(`socketID: ${socketID}'s receiverPeerConnection icecandidate`);
    socket.to(socketID).emit("getSenderCandidate", {
      candidate: e.candidate,
    });
  };

  pc.oniceconnectionstatechange = (e) => {
    //console.log(e);
  };

  pc.ontrack = (e) => {
    if (users[roomID]) { 
      if (!isIncluded(users[roomID], socketID)) { // Array<{id: string, stream: MediaStream}>
        users[roomID].push({
          id: socketID, // MedaStream 보내는 user의 socketID
          stream: e.streams[0], // user가 RTCPeerConnection을 통해 보내는 MediaStream
        });
      } else return;
    } else {
      users[roomID] = [
        {
          id: socketID,
          stream: e.streams[0],
        },
      ];
    }
    socket.broadcast.to(roomID).emit("userEnter", { id: socketID });
  };

  return pc;
};

const createSenderPeerConnection = (
  // senderSocketID를 socket id로 가진 user의 MediaStream,을 receiverSocketID를 socket id로 가진 user,에게 전달하기 위한 RTCPeerConnection을 생성하고,
  // 해당 RTCPeerConnection에 senderSocketID user의 veideotrack, audiotrack을 추가함
  receiverSocketID,
  senderSocketID,
  socket,
  roomID
) => {
  const pc = new wrtc.RTCPeerConnection(pc_config);

  if (senderPCs[senderSocketID]) {
    senderPCs[senderSocketID].filter((user) => user.id !== receiverSocketID);
    senderPCs[senderSocketID].push({ id: receiverSocketID, pc });
  } else
    senderPCs = {
      ...senderPCs,
      [senderSocketID]: [{ id: receiverSocketID, pc }], // Array<{id: string, pc: RTCPeerConnection}>
    };

  pc.onicecandidate = (e) => {
    //console.log(`socketID: ${receiverSocketID}'s senderPeerConnection icecandidate`);
    socket.to(receiverSocketID).emit("getReceiverCandidate", {
      id: senderSocketID,
      candidate: e.candidate,
    });
  };

  pc.oniceconnectionstatechange = (e) => {
    //console.log(e);
  };

  const sendUser = users[roomID].filter(
    (user) => user.id === senderSocketID
  )[0];
  sendUser.stream.getTracks().forEach((track) => {
    pc.addTrack(track, sendUser.stream);
  });

  return pc;
};

const getOtherUsersInRoom = (socketID, roomID) => {
  // 자신을 제외하고 roomID에 포함된 모든 유저의 socket id 배열을 반환
  let allUsers = [];

  if (!users[roomID]) return allUsers;

  allUsers = users[roomID]
    .filter((user) => user.id !== socketID)
    .map((otherUser) => ({ id: otherUser.id }));

  return allUsers;
};

const deleteUser = (socketID, roomID) => {
  // user의 정보가 포함된 목록에서 user를 제거함
  if (!users[roomID]) return;
  users[roomID] = users[roomID].filter((user) => user.id !== socketID);
  if (users[roomID].length === 0) {
    delete users[roomID];
  }
  delete socketToRoom[socketID]; // user가 속해 있는 roomID
};

const closeReceiverPC = (socketID) => {
  // socketID user가 자신의 MediaStream을 보내기 위해 연결한 RTCPeerConnection을 닫고, 목록에서 삭제함
  if (!receiverPCs[socketID]) return;

  receiverPCs[socketID].close();
  delete receiverPCs[socketID];
};

const closeSenderPCs = (socketID) => {
  // socketID user의 MedaiStream을 다른 user에게 전송하기 위해 연결 중이던  모든 RTCPeerConnection을 닫고, 목록에서 삭제함
  if (!senderPCs[socketID]) return;

  senderPCs[socketID].forEach((senderPC) => {
    senderPC.pc.close();
    const eachSenderPC = senderPCs[senderPC.id].filter(
      (sPC) => sPC.id === socketID
    )[0];
    if (!eachSenderPC) return;
    eachSenderPC.pc.close();
    senderPCs[senderPC.id] = senderPCs[senderPC.id].filter(
      (sPC) => sPC.id !== socketID
    );
  });

  delete senderPCs[socketID];
};

const io = socketio.listen(server);

io.sockets.on("connection", (socket) => {
  socket.on("joinRoom", (data) => { // data (id: room에 들어온 user의 socket id ,room: room id)
    // 기존에 room에 들어와 자신의 MediaStream을 서버에게 전송하고 있는 user들의 socket id 목록을, 지금 들어온 user에게 전송
    try {
      let allUsers = getOtherUsersInRoom(data.id, data.roomID);
      io.to(data.id).emit("allUsers", { users: allUsers });
    } catch (error) {
      console.log(error);
    }
  });

  socket.on("senderOffer", async (data) => { // data(senderSocketID, roomID, sdp: offer를 보내는 user의 RTCSessionDescription)
    // user의 MediaStream을 받을 RTCPeerConnection의 offer를 서버가 받고 answer를 보냄
    try {
      socketToRoom[data.senderSocketID] = data.roomID;
      let pc = createReceiverPeerConnection( // 
        data.senderSocketID,
        socket,
        data.roomID
      );
      await pc.setRemoteDescription(data.sdp);
      let sdp = await pc.createAnswer({
        offerToReceiveAudio: true, // user로부터 audio와 video stream을 모두 받아와야 하기 때문
        offerToReceiveVideo: true,
      });
      await pc.setLocalDescription(sdp);
      socket.join(data.roomID);
      io.to(data.senderSocketID).emit("getSenderAnswer", { sdp });
    } catch (error) {
      console.log(error);
    }
  });

  socket.on("senderCandidate", async (data) => { // data(senderSocketID, candidate: user의 RTCIceCandidate)
    // 해당 user가 offer를 보낼 때 저장해놓은 RTCPeerConnection에 RTCIceCandidate를 추가
    try {
      let pc = receiverPCs[data.senderSocketID];
      await pc.addIceCandidate(new wrtc.RTCIceCandidate(data.candidate));
    } catch (error) {
      console.log(error);
    }
  });

  socket.on("receiverOffer", async (data) => { // data(receiverSocketID: senderSocketID를 socket id로 가지는 user의 MediaStream을 받기 위한.., senderSocketID, roomID, sdp)
    try {
      // receiverSocketID를 socket id로 가지는 user가, senderSocketID를 socket id로 가지는 user의 MediaStream,을 받기 위한 RTCPeerConnection의 offer를 서버가 받고 answer를 보냄 
      let pc = createSenderPeerConnection(
        data.receiverSocketID,
        data.senderSocketID,
        socket,
        data.roomID
      );
      await pc.setRemoteDescription(data.sdp);
      let sdp = await pc.createAnswer({
        offerToReceiveAudio: false, // user로부터 audio와 video stream을 받지 않기 때문 -> 지금 생성한 RTCPeerConnection은 기존에 있던 user의 stream을 보내기 위한 연결
        offerToReceiveVideo: false,
      });
      await pc.setLocalDescription(sdp);
      io.to(data.receiverSocketID).emit("getReceiverAnswer", {
        id: data.senderSocketID,
        sdp,
      });
    } catch (error) {
      console.log(error);
    }
  });

  socket.on("receiverCandidate", async (data) => { // data(receiverSocketID, senderSocketID, candidate)
    // receiverSocketID를 socket id로 가지는 user,가 offer를 보낼 때 저장해놓은 RTCPeerConnection에 RTCIceCandidate를 추가
    try {
      const senderPC = senderPCs[data.senderSocketID].filter(
        (sPC) => sPC.id === data.receiverSocketID
      )[0];
      await senderPC.pc.addIceCandidate(
        new wrtc.RTCIceCandidate(data.candidate)
      );
    } catch (error) {
      console.log(error);
    }
  });

  socket.on("disconnect", () => {
    // disconnect된 user와 연결되어 있는 모든 RTCPeerConnection 및 MediaStream을 해제
    try {
      let roomID = socketToRoom[socket.id];

      deleteUser(socket.id, roomID);
      closeReceiverPC(socket.id);
      closeSenderPCs(socket.id);

      socket.broadcast.to(roomID).emit("userExit", { id: socket.id });
    } catch (error) {
      console.log(error);
    }
  });
});

server.listen(process.env.PORT || 8080, () => {
  console.log("server running on 8080");
});
