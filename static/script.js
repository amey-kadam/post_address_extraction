document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const fileLabel = document.getElementById('file-label');
    const uploadSection = document.getElementById('upload-section');
    const loading = document.querySelector('.loading');
  
    if (uploadForm) {
      uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!fileInput.files.length) return;
  
        uploadSection.style.display = 'none';
        loading.style.display = 'block';
  
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
  
        try {
          // Sending the file to the backend for address extraction
          const response = await fetch('/', {
            method: 'POST',
            body: formData
          });
  
          const result = await response.json();
          if (response.ok) {
            // Redirect to the results page with the extracted address
            const url = `/result?address=${encodeURIComponent(result.address)}`;
            window.location.href = url;
          } else {
            throw new Error(result.error || 'Failed to extract the address.');
          }
        } catch (error) {
          console.error('Error:', error);
          alert('There was an error processing your request.');
        } finally {
          loading.style.display = 'none';
        }
      });
  
      // Update file label when the user selects a file
      fileInput.addEventListener('change', () => {
        if (fileInput.files[0]) {
          fileLabel.textContent = fileInput.files[0].name;
        } else {
          fileLabel.textContent = 'Choose Image';
        }
      });
    }
  });
  