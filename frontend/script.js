const BACKEND_URL = "https://smartpdf-1uwd.onrender.com"

// File input handling
const pdfFileInput = document.getElementById("pdfFile")
const fileInfo = document.getElementById("fileInfo")
const uploadArea = document.getElementById("uploadArea")
const indexBtn = document.getElementById("indexBtn")
const analyzeBtn = document.getElementById("analyzeBtn")

pdfFileInput.addEventListener("change", handleFileSelect)

// Drag and drop functionality
uploadArea.addEventListener("dragover", (e) => {
  e.preventDefault()
  uploadArea.querySelector(".upload-label").style.borderColor = "var(--color-primary)"
  uploadArea.querySelector(".upload-label").style.background = "#eff6ff"
})

uploadArea.addEventListener("dragleave", () => {
  uploadArea.querySelector(".upload-label").style.borderColor = "var(--color-border)"
  uploadArea.querySelector(".upload-label").style.background = "var(--color-background)"
})

uploadArea.addEventListener("drop", (e) => {
  e.preventDefault()
  uploadArea.querySelector(".upload-label").style.borderColor = "var(--color-border)"
  uploadArea.querySelector(".upload-label").style.background = "var(--color-background)"

  const files = e.dataTransfer.files
  if (files.length > 0 && files[0].type === "application/pdf") {
    pdfFileInput.files = files
    handleFileSelect()
  } else {
    showStatus("indexStatus", "Please drop a valid PDF file", "error")
  }
})

function handleFileSelect() {
  const file = pdfFileInput.files[0]
  if (file) {
    const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2)
    fileInfo.textContent = `📄 ${file.name} (${fileSizeMB} MB)`
    fileInfo.classList.add("active")
  }
}

function indexPDF() {
  const statusBox = document.getElementById("indexStatus")

  if (pdfFileInput.files.length === 0) {
    showStatus("indexStatus", "Please select a PDF file first", "error")
    return
  }

  const file = pdfFileInput.files[0]
  const fileSizeMB = file.size / (1024 * 1024)

  if (fileSizeMB > 10) {
    showStatus("indexStatus", "File size exceeds 10MB limit", "error")
    return
  }

  const formData = new FormData()
  formData.append("pdf", file)

  // Update button state
  indexBtn.disabled = true
  indexBtn.classList.add("loading")
  indexBtn.innerHTML = `
        <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12a9 9 0 1 1-6.219-8.56"></path>
        </svg>
        Indexing Document...
    `

  showStatus("indexStatus", "Processing document... This may take a moment.", "info")

  fetch(`${BACKEND_URL}/index`, {
    method: "POST",
    body: formData,
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return response.json()
    })
    .then((data) => {
      showStatus("indexStatus", data.message || "Document indexed successfully! You can now ask questions.", "success")
      analyzeBtn.disabled = false
    })
    .catch((err) => {
      console.error("Indexing error:", err)
      showStatus("indexStatus", "Error indexing document. Please ensure the backend server is running.", "error")
    })
    .finally(() => {
      // Reset button state
      indexBtn.disabled = false
      indexBtn.classList.remove("loading")
      indexBtn.innerHTML = `
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            Index Document
        `
    })
}

function askQuestion() {
  const question = document.getElementById("question").value.trim()
  const answerBox = document.getElementById("answerBox")
  const answerContainer = document.getElementById("answerContainer")

  if (!question) {
    alert("Please enter a question before analyzing")
    return
  }

  // Update button state
  analyzeBtn.disabled = true
  analyzeBtn.classList.add("loading")
  analyzeBtn.innerHTML = `
        <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12a9 9 0 1 1-6.219-8.56"></path>
        </svg>
        Analyzing...
    `

  // Show answer container with loading state
  answerContainer.style.display = "block"
  answerBox.textContent = "Analyzing your question and searching the document..."

  fetch(`${BACKEND_URL}/chat?question=${encodeURIComponent(question)}`, {
    method: "POST",
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return response.json()
    })
    .then((data) => {
       answerBox.innerHTML = marked.parse(data.answer || "No answer received from the server.")
    })
    .catch((err) => {
      console.error("Analysis error:", err)
      answerBox.textContent =
        "Error getting response. Please ensure:\n1. The document has been indexed\n2. The backend server is running\n3. Your question is clear and relevant to the document"
    })
    .finally(() => {
      // Reset button state
      analyzeBtn.disabled = false
      analyzeBtn.classList.remove("loading")
      analyzeBtn.innerHTML = `
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2a10 10 0 0 1 7.38 16.75l2.37 2.37a1 1 0 0 1-1.41 1.41l-2.37-2.37A10 10 0 1 1 12 2z"></path>
                <path d="M12 8v4"></path>
                <path d="M12 16h.01"></path>
            </svg>
            Analyze Contract
        `
    })
}

function showStatus(elementId, message, type) {
  const statusBox = document.getElementById(elementId)
  statusBox.textContent = message
  statusBox.className = `status-message active ${type}`

  // Auto-hide after 5 seconds for non-error messages
  if (type !== "error") {
    setTimeout(() => {
      statusBox.classList.remove("active")
    }, 5000)
  }
}

// Initialize analyze button as disabled
analyzeBtn.disabled = true
