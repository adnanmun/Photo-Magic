const fileInput = document.getElementById('file-input');
const brightnessInput = document.getElementById('brightness');
const contrastInput = document.getElementById('contrast');
const imagePreview = document.getElementById('image-preview');
const downloadBtn = document.getElementById('download-btn');

let uploadedImage = null;
let editedImage = null;

fileInput.addEventListener('change', () => {
    const file = fileInput.files[0];
    const reader = new FileReader();
    reader.onload = (e) => {
        uploadedImage = e.target.result.split(',')[1];
        imagePreview.src = e.target.result;
        adjustImage();
    };
    reader.readAsDataURL(file);
});

function adjustImage() {
    if (!uploadedImage) return;
    
    const brightness = brightnessInput.value;
    const contrast = contrastInput.value;

    $.ajax({
        method: 'POST',
        url: '/adjust',
        contentType: 'application/json',
        data: JSON.stringify({
            image: uploadedImage,
            brightness: brightness,
            contrast: contrast
        }),
        success: function(data) {
            if (data.error) {
                console.error(data.error);
            } else {
                editedImage = 'data:image/jpeg;base64,' + data.image;
                imagePreview.src = editedImage;
                downloadBtn.style.display = 'block';
            }
        },
        error: function(jqXHR, textStatus, errorThrown) {
            console.error(`Error during AJAX request: ${textStatus}`, errorThrown);
        }
    });
}

brightnessInput.addEventListener('input', adjustImage);
contrastInput.addEventListener('input', adjustImage);

downloadBtn.addEventListener('click', () => {
    if (editedImage) {
        const a = document.createElement('a');
        a.href = editedImage;
        a.download = 'edited_image.jpg';
        a.click();
    }
});
