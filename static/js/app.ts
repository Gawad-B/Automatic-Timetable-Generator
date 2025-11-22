// Type definitions
interface FileUploadStatus {
    courses: File | null;
    instructors: File | null;
    rooms: File | null;
    timeslots: File | null;
    sections: File | null;
}

interface UploadResponse {
    success: boolean;
    message?: string;
    total_assignments?: number;
    total_files?: number;
    generation_time?: number;
}

// State management
class TimetableGenerator {
    private uploadedFiles: FileUploadStatus;
    private isGenerating: boolean;
    private startTime: number;

    constructor() {
        this.uploadedFiles = {
            courses: null,
            instructors: null,
            rooms: null,
            timeslots: null,
            sections: null
        };
        this.isGenerating = false;
        this.startTime = 0;
        this.initializeEventListeners();
        this.setupDragAndDrop();
    }

    private initializeEventListeners(): void {
        // File input listeners
        const fileInputs: Array<keyof FileUploadStatus> = ['courses', 'instructors', 'rooms', 'timeslots', 'sections'];
        
        fileInputs.forEach(type => {
            const fileInput = document.getElementById(`${type}-file`) as HTMLInputElement;
            if (fileInput) {
                fileInput.addEventListener('change', (e) => this.handleFileSelect(e, type));
            }
        });

        // Generate button listener
        const generateBtn = document.getElementById('generate-btn') as HTMLButtonElement;
        if (generateBtn) {
            generateBtn.addEventListener('click', () => this.generateTimetable());
        }

        // Download button listener
        const downloadBtn = document.getElementById('download-btn') as HTMLButtonElement;
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => this.downloadTimetable());
        }
    }

    private setupDragAndDrop(): void {
        const uploadZones = document.querySelectorAll('.upload-zone');
        
        uploadZones.forEach(zone => {
            zone.addEventListener('dragover', (e) => {
                e.preventDefault();
                zone.classList.add('dragover');
            });

            zone.addEventListener('dragleave', () => {
                zone.classList.remove('dragover');
            });

            zone.addEventListener('drop', (e) => {
                e.preventDefault();
                zone.classList.remove('dragover');
                
                const target = (zone as HTMLElement).dataset.target as keyof FileUploadStatus;
                const files = (e as DragEvent).dataTransfer?.files;
                
                if (files && files.length > 0) {
                    this.handleFileDrop(files[0], target);
                }
            });
        });
    }

    private handleFileSelect(event: Event, type: keyof FileUploadStatus): void {
        const input = event.target as HTMLInputElement;
        if (input.files && input.files.length > 0) {
            this.handleFileDrop(input.files[0], type);
        }
    }

    private handleFileDrop(file: File, type: keyof FileUploadStatus): void {
        // Validate file type
        if (!file.name.endsWith('.csv')) {
            this.showNotification('Please upload a CSV file', 'error');
            return;
        }

        // Store the file
        this.uploadedFiles[type] = file;

        // Update UI
        this.updateFileStatus(type, file.name);
        this.checkAllFilesUploaded();
    }

    private updateFileStatus(type: keyof FileUploadStatus, filename: string): void {
        const statusDot = document.getElementById(`${type}-status`);
        const filenameSpan = document.getElementById(`${type}-filename`);

        if (statusDot && filenameSpan) {
            statusDot.className = 'status-dot status-success';
            filenameSpan.textContent = filename;
            
            // Animate the change
            const card = statusDot.closest('.upload-zone');
            if (card) {
                card.classList.add('pulse-glow');
                setTimeout(() => card.classList.remove('pulse-glow'), 1000);
            }
        }
    }

    private checkAllFilesUploaded(): void {
        const allUploaded = Object.values(this.uploadedFiles).every(file => file !== null);
        const generateBtn = document.getElementById('generate-btn') as HTMLButtonElement;
        const uploadStatus = document.getElementById('upload-status');

        if (generateBtn && uploadStatus) {
            generateBtn.disabled = !allUploaded;
            
            if (allUploaded) {
                uploadStatus.textContent = 'All files uploaded! Ready to generate';
                uploadStatus.classList.add('text-green-300');
            } else {
                const remaining = Object.entries(this.uploadedFiles)
                    .filter(([_, file]) => file === null)
                    .map(([type, _]) => type)
                    .join(', ');
                uploadStatus.textContent = `Missing: ${remaining}`;
            }
        }
    }

    private async generateTimetable(): Promise<void> {
        if (this.isGenerating) return;

        this.isGenerating = true;
        this.startTime = Date.now();

        // Show progress section
        const progressSection = document.getElementById('progress-section');
        const generateBtn = document.getElementById('generate-btn') as HTMLButtonElement;
        const btnText = document.getElementById('btn-text');
        const btnSpinner = document.getElementById('btn-spinner');

        if (progressSection) progressSection.classList.remove('hidden');
        if (generateBtn) generateBtn.disabled = true;
        if (btnText) btnText.textContent = 'Generating...';
        if (btnSpinner) btnSpinner.classList.remove('hidden');

        // Simulate progress
        this.simulateProgress();

        try {
            // Create FormData
            const formData = new FormData();
            Object.entries(this.uploadedFiles).forEach(([type, file]) => {
                if (file) {
                    formData.append(type, file);
                }
            });

            // Upload files
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Upload failed');
            }

            // Generate timetable
            const generateResponse = await fetch('/generate', {
                method: 'POST'
            });

            if (!generateResponse.ok) {
                throw new Error('Generation failed');
            }

            const result: UploadResponse = await generateResponse.json();

            if (result.success) {
                this.showSuccess(result);
            } else {
                throw new Error(result.message || 'Generation failed');
            }

        } catch (error) {
            console.error('Error:', error);
            this.showNotification('Failed to generate timetable. Please try again.', 'error');
            this.resetUI();
        }
    }

    private simulateProgress(): void {
        const progressBar = document.getElementById('progress-bar');
        const progressText = document.getElementById('progress-text');
        
        const steps = [
            { progress: 20, text: 'Uploading files...' },
            { progress: 40, text: 'Parsing data...' },
            { progress: 60, text: 'Initializing CSP solver...' },
            { progress: 80, text: 'Solving constraints...' },
            { progress: 95, text: 'Generating Excel files...' }
        ];

        let currentStep = 0;
        const interval = setInterval(() => {
            if (currentStep < steps.length) {
                const step = steps[currentStep];
                if (progressBar) progressBar.style.width = `${step.progress}%`;
                if (progressText) progressText.textContent = step.text;
                currentStep++;
            } else {
                clearInterval(interval);
            }
        }, 800);
    }

    private showSuccess(result: UploadResponse): void {
        const progressSection = document.getElementById('progress-section');
        const successSection = document.getElementById('success-section');
        const progressBar = document.getElementById('progress-bar');

        // Complete progress bar
        if (progressBar) progressBar.style.width = '100%';

        setTimeout(() => {
            if (progressSection) progressSection.classList.add('hidden');
            if (successSection) successSection.classList.remove('hidden');

            // Update stats
            const totalAssignments = document.getElementById('total-assignments');
            const totalFiles = document.getElementById('total-files');
            const generationTime = document.getElementById('generation-time');

            if (totalAssignments) totalAssignments.textContent = (result.total_assignments || 0).toString();
            if (totalFiles) totalFiles.textContent = (result.total_files || 0).toString();
            if (generationTime) {
                const elapsed = ((Date.now() - this.startTime) / 1000).toFixed(1);
                generationTime.textContent = `${elapsed}s`;
            }

            this.isGenerating = false;
        }, 500);
    }

    private downloadTimetable(): void {
        window.location.href = '/download';
    }

    private resetUI(): void {
        const generateBtn = document.getElementById('generate-btn') as HTMLButtonElement;
        const btnText = document.getElementById('btn-text');
        const btnSpinner = document.getElementById('btn-spinner');
        const progressSection = document.getElementById('progress-section');

        if (generateBtn) generateBtn.disabled = false;
        if (btnText) btnText.textContent = 'Generate Timetable';
        if (btnSpinner) btnSpinner.classList.add('hidden');
        if (progressSection) progressSection.classList.add('hidden');

        this.isGenerating = false;
    }

    private showNotification(message: string, type: 'success' | 'error'): void {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 glass-card rounded-lg p-4 shadow-2xl slide-up z-50 ${
            type === 'success' ? 'border-green-500' : 'border-red-500'
        } border-l-4`;
        
        notification.innerHTML = `
            <div class="flex items-center space-x-3">
                <div class="flex-shrink-0">
                    ${type === 'success' 
                        ? '<svg class="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>'
                        : '<svg class="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>'
                    }
                </div>
                <p class="text-white font-medium">${message}</p>
            </div>
        `;

        document.body.appendChild(notification);

        // Auto remove after 3 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new TimetableGenerator();
    });
} else {
    new TimetableGenerator();
}
