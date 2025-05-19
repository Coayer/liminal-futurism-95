document.addEventListener("DOMContentLoaded", () => {
    let idleMouseTimer;
    let forceMouseHide = false;

    document.body.style.cursor = "none";

    document.body.addEventListener("mousemove", () => {
        if (forceMouseHide) {
            return;
        }

        document.body.style.cursor = "";

        clearTimeout(idleMouseTimer);

        idleMouseTimer = setTimeout(() => {
            document.body.style.cursor = "none";

            forceMouseHide = true;

            setTimeout(() => {
                forceMouseHide = false;
            }, 200);
        }, 1000);
    });

    const splashScreen = document.getElementById("splash-screen");
    const slideshow = document.getElementById("slideshow");
    const currentImage = document.getElementById("current-image");
    let audio = null;
    let previousAudioUrl = null;

    // Initialize the slideshow when the user clicks
    document.body.addEventListener("click", startSlideshow, { once: true });

    function startSlideshow() {
        console.log("Starting slideshow");
        splashScreen.classList.add("hidden");
        slideshow.classList.remove("hidden");

        // Initialize audio
        audio = new Audio();
        audio.autoplay = true;

        // Show the first slide
        showNextSlide();
    }

    function showNextSlide() {
        console.log("Loading next slide");
        // Fade out the current image
        currentImage.classList.remove("fade-in");
        currentImage.classList.add("fade-out");

        setTimeout(() => {
            try {
                // Fetch next image and audio from server endpoints
                fetchNextImage();
                fetchNextAudio();

                // Schedule the next slide after 6 seconds
                setTimeout(showNextSlide, 6000);
            } catch (error) {
                console.error("Error in showNextSlide:", error);
            }
        }, 2000); // Wait for fade out to complete
    }

    function fetchNextImage() {
        // Add timestamp to prevent caching
        const imageUrl = `${document.location.origin}/image?t=${Date.now()}`;

        currentImage.onload = () => {
            console.log("Image loaded successfully");
            currentImage.classList.remove("fade-out");
            currentImage.classList.add("fade-in");
        };

        currentImage.src = imageUrl;
    }

    function fetchNextAudio() {
        // Add timestamp to prevent caching
        const audioFiles = [
            "-5.wav",
            "-4.wav",
            "-3.wav",
            "-2.wav",
            "-1.wav",
            "0.wav",
            "+1.wav",
            "+2.wav",
            "+3.wav",
        ];

        let audioUrl = previousAudioUrl;

        while (audioUrl === previousAudioUrl) {
            audioUrl = createAudioUrl(
                audioFiles[Math.floor(Math.random() * audioFiles.length)]
            );
        }

        if (previousAudioUrl === null) {
            audioUrl = createAudioUrl("0.wav");
        }

        console.log("Fetching audio from:", audioUrl);

        audio.src = audioUrl;
        audio.play();

        previousAudioUrl = audioUrl;

        function createAudioUrl(filename) {
            return `${document.location.origin}/static/audio/${filename}`;
        }
    }
});
