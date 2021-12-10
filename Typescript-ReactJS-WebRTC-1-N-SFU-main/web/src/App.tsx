import React, { useState, useRef, useEffect, useCallback } from "react";
import io from "socket.io-client";
import Video from "./Components/Video";
import { WebRTCUser } from "./types";

const pc_config = { // pc_config변수: RTCPeerConnection 생성 시의 setting
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
const SOCKET_SERVER_URL = "http://localhost:8080";

const App = () => {
  const socketRef = useRef<SocketIOClient.Socket>(); // socket 변수 : 서버와 통신할 소켓(SocketIOClinet.Socket)
  const localStreamRef = useRef<MediaStream>();
  const sendPCRef = useRef<RTCPeerConnection>(); // sendPC 변수 : 자신의 MediaStream을 서버에게 전송할 RTCPeerConnection
  const receivePCsRef = useRef<{ [socketId: string]: RTCPeerConnection }>({}); // 같은 room에 참가한 다른 user들의 MediaStream을 서버에서 전송받을 RTCPeerConnection 목록(receivePCs[socket id] = pc형식)
  const [users, setUsers] = useState<Array<WebRTCUser>>([]); // users 변수: 상대방의 데이터(socket id, MediaStream) 배열

  const localVideoRef = useRef<HTMLVideoElement>(null); // 자신의 MediaStream을 출력할 video 태그의 ref

  const closeReceivePC = useCallback((id: string) => {
    if (!receivePCsRef.current[id]) return;
    receivePCsRef.current[id].close();
    delete receivePCsRef.current[id];
  }, []);

  const createReceiverOffer = useCallback(
    async (pc: RTCPeerConnection, senderSocketID: string) => {
      try {
        const sdp = await pc.createOffer({
          offerToReceiveAudio: true,
          offerToReceiveVideo: true,
        });
        console.log("create receiver offer success");
        await pc.setLocalDescription(new RTCSessionDescription(sdp));

        if (!socketRef.current) return;
        socketRef.current.emit("receiverOffer", {
          sdp,
          receiverSocketID: socketRef.current.id,
          senderSocketID,
          roomID: "1234",
        });
      } catch (error) {
        console.log(error);
      }
    },
    []
  );

  const createReceiverPeerConnection = useCallback((socketID: string) => {
    try {
      const pc = new RTCPeerConnection(pc_config); 

      // add pc to peerConnections object
      receivePCsRef.current = { ...receivePCsRef.current, [socketID]: pc };

      pc.onicecandidate = (e) => {
        if (!(e.candidate && socketRef.current)) return;
        console.log("receiver PC onicecandidate");
        socketRef.current.emit("receiverCandidate", {
          candidate: e.candidate,
          receiverSocketID: socketRef.current.id,
          senderSocketID: socketID,
        });
      };

      pc.oniceconnectionstatechange = (e) => {
        console.log(e);
      };

      pc.ontrack = (e) => {
        console.log("ontrack success");
        setUsers((oldUsers) =>
          oldUsers
            .filter((user) => user.id !== socketID)
            .concat({
              id: socketID,
              stream: e.streams[0],
            })
        );
      };

      // return pc
      return pc;
    } catch (e) {
      console.error(e);
      return undefined;
    }
  }, []);

  const createReceivePC = useCallback( // room에 참가한 다른 user들의 MediaStream을 받을 RTCPeerConnection을 생성하고, 서버에 offer를 보냄 
    (id: string) => {
      try {
        console.log(`socketID(${id}) user entered`);
        const pc = createReceiverPeerConnection(id);
        if (!(socketRef.current && pc)) return;
        createReceiverOffer(pc, id);
      } catch (error) {
        console.log(error);
      }
    },
    [createReceiverOffer, createReceiverPeerConnection]
  );

  const createSenderOffer = useCallback(async () => { 
    // 자신의 MediaStream을 서버에게 보낼 RTCPeerConnection의 offer를 생성
    // RTCSessionDescriptrion을 해당 RTCPeerConnection의 localDescription에 지정
    // RTCSessionDescription을 소켓을 통해 서버로 전송
    try {
      if (!sendPCRef.current) return;
      const sdp = await sendPCRef.current.createOffer({
        offerToReceiveAudio: false, // MediaStream을 보내기 위한 RTCPeerConnection이므로 모두 false로 둠
        offerToReceiveVideo: false,
      });
      console.log("create sender offer success");
      await sendPCRef.current.setLocalDescription(
        new RTCSessionDescription(sdp)
      );

      if (!socketRef.current) return;
      socketRef.current.emit("senderOffer", {
        sdp,
        senderSocketID: socketRef.current.id,
        roomID: "1234",
      });
    } catch (error) {
      console.log(error);
    }
  }, []);

  const createSenderPeerConnection = useCallback(() => {
    const pc = new RTCPeerConnection(pc_config);

    pc.onicecandidate = (e) => {
      if (!(e.candidate && socketRef.current)) return;
      console.log("sender PC onicecandidate");
      socketRef.current.emit("senderCandidate", {
        candidate: e.candidate,
        senderSocketID: socketRef.current.id,
      });
    };

    pc.oniceconnectionstatechange = (e) => {
      console.log(e);
    };

    if (localStreamRef.current) {
      console.log("add local stream");
      localStreamRef.current.getTracks().forEach((track) => {
        if (!localStreamRef.current) return;
        pc.addTrack(track, localStreamRef.current);
      });
    } else {
      console.log("no local stream");
    }

    sendPCRef.current = pc;
  }, []);

  const getLocalStream = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        // 이 함수를 호출해서 자신의 MediaStream을 얻고, localVideoRef에 등록함
        // 자신의 MediaStream을 전송할 RTCPeerConnection을 생성하고, 서버에게 offer를 보냄
        // 자신이 room에 참가했다고 서버에 알람 (이후에 allUsers socket 이벤트로 답이 옴)
        audio: true,
        video: {
          width: 240,
          height: 240,
        },
      });
      localStreamRef.current = stream;
      if (localVideoRef.current) localVideoRef.current.srcObject = stream;
      if (!socketRef.current) return;

      createSenderPeerConnection();
      await createSenderOffer();

      socketRef.current.emit("joinRoom", {
        id: socketRef.current.id,
        roomID: "1234",
      });
    } catch (e) {
      console.log(`getUserMedia error: ${e}`);
    }
  }, [createSenderOffer, createSenderPeerConnection]);

  useEffect(() => {
    socketRef.current = io.connect(SOCKET_SERVER_URL);
    getLocalStream();

    socketRef.current.on("userEnter", (data: { id: string }) => { // (id: 같은 room에 참가하고 자신의 MedaiStream을 전송할 RTCPeerConnection을 서버와 연결한 user의 socket id)
      // 해당 user의 MediaStream을 받을 RTCPeerConnection을 생성하고, 서버로 offer를 보냄
      createReceivePC(data.id);
    });

    socketRef.current.on(
      "allUsers",
      (data: { users: Array<{ id: string }> }) => { // (users: 기존에 방에 참가해서 자신의 MediaStream을 전송할 RTCPeerConnection을 서버와 연결한, user들의 socket id 배열)
        // 해당 user들의 MediaStream을 받을 RTCPeerConnection을 생성하고, 서버로 offer를 보냄
        data.users.forEach((user) => createReceivePC(user.id));
      }
    );

    socketRef.current.on("userExit", (data: { id: string }) => { // (id: dosconnect된 user의 socket id)
      // 해당 user의 MediaStream을 받기 위해 연결한 RTCPeerConnection을 닫고, 목록에서 삭제
      closeReceivePC(data.id);
      setUsers((users) => users.filter((user) => user.id !== data.id));
    });

    socketRef.current.on(
      "getSenderAnswer",
      async (data: { sdp: RTCSessionDescription }) => { // (sdp: 자신의 MediaStream을 서버로 보내기 위해 offer를 보낸 RTCPeerConnection에 대한 answer로 온 RTCSessionDescription)
        // 해당 RTCPeerConnection의 remoteDescription으로 sdp를 지정
        try {
          if (!sendPCRef.current) return;
          console.log("get sender answer");
          console.log(data.sdp);
          await sendPCRef.current.setRemoteDescription(
            new RTCSessionDescription(data.sdp)
          );
        } catch (error) {
          console.log(error);
        }
      }
    );

    socketRef.current.on(
      "getSenderCandidate",
      async (data: { candidate: RTCIceCandidateInit }) => { // (candidate: 자신의 MediaStream을 서버로 보내기 위한 RTCPeerConnection을 위해 서버에서 보낸 RTIceCandidate)
        // 해당 RTCPeerConnection에 RTCIceCandidate 추가
        try {
          if (!(data.candidate && sendPCRef.current)) return;
          console.log("get sender candidate");
          await sendPCRef.current.addIceCandidate(
            new RTCIceCandidate(data.candidate)
          );
          console.log("candidate add success");
        } catch (error) {
          console.log(error);
        }
      }
    );

    socketRef.current.on(
      "getReceiverAnswer",
      async (data: { id: string; sdp: RTCSessionDescription }) => { // (id: 전송받을 MediaStream의 주인인 user의 socket id, sdp: 전송받을 MediaStream의 RTCPeerConection의 offer에 대한 answer로 온 RTCSesionDescription)
        // 해당 RTCPeerConnection의 remoteDescription으로 sdp를 지정
        try {
          console.log(`get socketID(${data.id})'s answer`);
          const pc: RTCPeerConnection = receivePCsRef.current[data.id];
          if (!pc) return;
          await pc.setRemoteDescription(data.sdp);
          console.log(`socketID(${data.id})'s set remote sdp success`);
        } catch (error) {
          console.log(error);
        }
      }
    );

    socketRef.current.on(
      "getReceiverCandidate",
      async (data: { id: string; candidate: RTCIceCandidateInit }) => { // (candidateL 전송받을 MedaiStream의 RTCPeerConnection을 위해 서버에서 보낸 RTCIceCandidate)
        // 해당 RTCPeerConnection에 RTCIceCandidate 추가
        try {
          console.log(data);
          console.log(`get socketID(${data.id})'s candidate`);
          const pc: RTCPeerConnection = receivePCsRef.current[data.id];
          if (!(pc && data.candidate)) return;
          await pc.addIceCandidate(new RTCIceCandidate(data.candidate));
          console.log(`socketID(${data.id})'s candidate add success`);
        } catch (error) {
          console.log(error);
        }
      }
    );

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
      if (sendPCRef.current) {
        sendPCRef.current.close();
      }
      users.forEach((user) => closeReceivePC(user.id));
    };
    // eslint-disable-next-line
  }, [
    closeReceivePC,
    createReceivePC,
    createSenderOffer,
    createSenderPeerConnection,
    getLocalStream,
  ]);

  return (
    <div>
      <video
        style={{
          width: 240,
          height: 240,
          margin: 5,
          backgroundColor: "black",
        }}
        muted
        ref={localVideoRef}
        autoPlay
      />
      {users.map((user, index) => (
        <Video key={index} stream={user.stream} />
      ))}
    </div>
  );
};

export default App;
