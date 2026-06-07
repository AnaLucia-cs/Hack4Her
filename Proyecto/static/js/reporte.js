async function playAudio() {
    const res = await fetch("/generate-audio");
    const data = await res.json();

    const audio = new Audio(data.url + "?t=" + Date.now());
    audio.play();
}