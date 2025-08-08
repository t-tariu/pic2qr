
const imageInput = document.getElementById('image');
const dataInput = document.getElementById('data');
const form = document.getElementById('qr-form');
const progressSteps = document.querySelectorAll('.progress-step');
const activeProgressLine = document.getElementById('progress-line-active');
const updateTotalProgress = () => {
    let currentStep = 1; // The step the user is currently on
    if (imageInput.files.length > 0) {
        currentStep = 2;
    }
    if (imageInput.files.length > 0 && dataInput.value.trim() !== '') {
        currentStep = 3;
    }
    // Step 4 (Completion) is handled on submit
    const totalSegments = progressSteps.length - 1;
    const completedSegments = currentStep - 1;
    const progressWidth = totalSegments > 0 ? (completedSegments / totalSegments) * 100 : 0;
    activeProgressLine.style.width = `${progressWidth}%`;
    progressSteps.forEach((step, index) => {
        // index is 0-based, currentStep is 1-based
        if (index < currentStep) {
            step.classList.add('active');
        } else {
            step.classList.remove('active');
        }
    });
};
imageInput.addEventListener('change', updateTotalProgress);
dataInput.addEventListener('input', updateTotalProgress);
form.addEventListener('submit', async function(e) {
    e.preventDefault();
    const formData = new FormData(form);
    const loader = document.getElementById('loader');
    const resultDiv = document.getElementById('qr-result');
    const qrImage = document.getElementById('qr-image');
    const downloadBtn = document.getElementById('download-btn');
    const downloadLink = document.getElementById('download-link');
    const resultTitle = document.getElementById('result-title');

    loader.style.display = 'block';
    resultDiv.style.display = 'none';
    downloadBtn.style.display = 'none';
    resultTitle.style.display = 'block';
    
    // Mark final step as active
    progressSteps[3].classList.add('active');
    activeProgressLine.style.width = '100%';
    try {
        const response = await fetch('/generate-qr', {
            method: 'POST',
            body: formData
        });
        if (!response.ok) {
            let errorDetail = 'QR 코드 생성에 실패했습니다.';
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.indexOf("application/json") !== -1) {
                const error = await response.json();
                errorDetail = error.detail || errorDetail;
            } else {
                errorDetail = await response.text();
            }
            throw new Error(errorDetail);
        }
        const imageBlob = await response.blob();
        const imageUrl = URL.createObjectURL(imageBlob);

        qrImage.src = imageUrl;
        downloadLink.href = imageUrl;
        downloadLink.download = 'qrcode.gif'; // Set a default filename
        resultDiv.style.display = 'block';
        downloadBtn.style.display = 'block';
        resultTitle.style.display = 'none';
    } catch (error) {
        alert(error.message);
        resultTitle.style.display = 'block';
        // Revert progress if submission fails
        progressSteps[3].classList.remove('active'); // Un-complete the final step
        updateTotalProgress();
    } finally {
        loader.style.display = 'none';
    }
});
// Initial progress state on page load
updateTotalProgress();
// Modal script
const navLinks = document.querySelectorAll('.nav-link[data-modal]');
const modals = document.querySelectorAll('.modal');
const closeBtns = document.querySelectorAll('.close-btn');
navLinks.forEach(link => {
    link.addEventListener('click', () => {
        const modalId = link.getAttribute('data-modal');
        document.getElementById(modalId).style.display = 'block';
    });
});
closeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        btn.closest('.modal').style.display = 'none';
    });
});
window.addEventListener('click', (event) => {
    modals.forEach(modal => {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    });
});
