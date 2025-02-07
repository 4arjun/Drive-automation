import React, { useState, useRef } from "react";
import axios from "axios";

const Recorder = () => {
    const [recording, setRecording] = useState(false);
    const mediaRecorderRef = useRef(null);
    const chunksRef = useRef([]);
    const streamRef = useRef(null);

    const startRecording = async () => {
        try {
            const screenStream = await navigator.mediaDevices.getDisplayMedia({
                video: {
                    width: { ideal: 1920 }, 
                    height: { ideal: 1080 },
                    frameRate: { ideal: 60, max: 60 }, 
                    bitrate: 10000000
                }
            });
    
            const audioStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true, 
                    noiseSuppression: true,
                    sampleRate: 48000, 
                    channelCount: 2 
                }
            });
    
            const combinedStream = new MediaStream([
                ...screenStream.getVideoTracks(),
                ...audioStream.getAudioTracks()
            ]);
    
            streamRef.current = { screenStream, audioStream }; 
            const mediaRecorder = new MediaRecorder(combinedStream, { mimeType: "video/webm" });
    
            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    chunksRef.current.push(event.data);
                }
            };
    
            mediaRecorder.onstop = async () => {
                const blob = new Blob(chunksRef.current, { type: "video/webm" });
                const file = new File([blob], "screen_recording.webm", { type: "video/webm" });
    
                await uploadToServer(file);
                chunksRef.current = []; 
            };
    
            mediaRecorderRef.current = mediaRecorder;
            mediaRecorder.start();
            setRecording(true);
        } catch (error) {
            console.error("Error starting recording:", error);
        }
    };
    

    const stopRecording = () => {
        mediaRecorderRef.current?.stop();
        setRecording(false);

        streamRef.current?.screenStream?.getTracks().forEach(track => track.stop());
        streamRef.current?.audioStream?.getTracks().forEach(track => track.stop());
    };

    const uploadToServer = async (file) => {
        const formData = new FormData();
        formData.append("video", file);

        try {
            const response = await axios.post("http://127.0.0.1:8000/api/upload/", formData, {
                headers: { "Content-Type": "multipart/form-data" }
            });

            alert(`Upload Successful! File ID: ${response.data.fileId}`);
        } catch (error) {
            console.error("Upload failed:", error);
        }
    };

    return (
        <div>
            <h2>Screen & Audio Recorder</h2>
            <button onClick={recording ? stopRecording : startRecording}>
                {recording ? "Stop Recording" : "Start Recording"}
            </button>
        </div>
    );
};

export default Recorder;
