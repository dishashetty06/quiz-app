class QuizTimer {
    constructor(initialSeconds, displayElement, progressBarElement, onTimeUp) {
        this.remainingSeconds = initialSeconds;
        this.displayElement = displayElement;
        this.progressBarElement = progressBarElement;
        this.onTimeUp = onTimeUp;
        this.initialSeconds = initialSeconds;
        this.timerInterval = null;
        this.warningThreshold = Math.min(60, Math.floor(initialSeconds * 0.2)); // 20% of time or 60 seconds, whichever is less
        this.criticalThreshold = Math.min(30, Math.floor(initialSeconds * 0.1)); // 10% of time or 30 seconds, whichever is less
    }

    start() {
        // Initial update before starting interval
        this.update();
        
        // Set interval to update every second
        this.timerInterval = setInterval(() => {
            this.remainingSeconds--;
            this.update();
            
            if (this.remainingSeconds <= 0) {
                this.stop();
                if (this.onTimeUp && typeof this.onTimeUp === 'function') {
                    this.onTimeUp();
                }
            }
        }, 1000);
    }

    update() {
        // Format time as MM:SS
        const minutes = Math.floor(this.remainingSeconds / 60);
        const seconds = this.remainingSeconds % 60;
        const formattedTime = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        // Update display element
        if (this.displayElement) {
            this.displayElement.textContent = formattedTime;
            
            // Update color based on remaining time
            this.displayElement.className = 'timer-display'; // Reset class
            if (this.remainingSeconds <= this.criticalThreshold) {
                this.displayElement.classList.add('critical');
            } else if (this.remainingSeconds <= this.warningThreshold) {
                this.displayElement.classList.add('warning');
            }
        }
        
        // Update progress bar if present
        if (this.progressBarElement) {
            const percentage = (this.remainingSeconds / this.initialSeconds) * 100;
            this.progressBarElement.style.width = `${percentage}%`;
            
            // Update progress bar color
            this.progressBarElement.className = 'progress-bar'; // Reset class
            if (this.remainingSeconds <= this.criticalThreshold) {
                this.progressBarElement.classList.add('bg-danger');
            } else if (this.remainingSeconds <= this.warningThreshold) {
                this.progressBarElement.classList.add('bg-warning');
            } else {
                this.progressBarElement.classList.add('bg-success');
            }
        }
    }

    stop() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }

    pause() {
        this.stop();
    }

    resume() {
        if (!this.timerInterval && this.remainingSeconds > 0) {
            this.start();
        }
    }

    reset(newSeconds = null) {
        this.stop();
        this.remainingSeconds = newSeconds !== null ? newSeconds : this.initialSeconds;
        this.update();
    }

    getTimeLeft() {
        return this.remainingSeconds;
    }

    // Returns formatted time string
    getFormattedTimeLeft() {
        const minutes = Math.floor(this.remainingSeconds / 60);
        const seconds = this.remainingSeconds % 60;
        return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }

    // Add time (in seconds)
    addTime(seconds) {
        this.remainingSeconds += seconds;
        this.update();
    }
    
    // Subtract time (in seconds)
    subtractTime(seconds) {
        this.remainingSeconds = Math.max(0, this.remainingSeconds - seconds);
        this.update();
        
        if (this.remainingSeconds <= 0) {
            this.stop();
            if (this.onTimeUp && typeof this.onTimeUp === 'function') {
                this.onTimeUp();
            }
        }
    }
}