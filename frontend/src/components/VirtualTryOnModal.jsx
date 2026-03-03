import React, { useState, useRef } from "react";
import "./VirtualTryOnModal.css";

export default function VirtualTryOnModal({ product, onClose }) {
  const [personImage, setPersonImage] = useState(null);
  const [personPreview, setPersonPreview] = useState(null);
  const [resultImage, setResultImage] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileSelect = (file) => {
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      setError("Please upload a valid image file (JPG, PNG, etc.)");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError("Image size must be less than 10MB");
      return;
    }
    setError("");
    setPersonImage(file);
    setResultImage(null);
    const reader = new FileReader();
    reader.onloadend = () => setPersonPreview(reader.result);
    reader.readAsDataURL(file);
  };

  const handleInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleTryOn = async () => {
    if (!personImage) {
      setError("Please upload your photo first");
      return;
    }
    setIsLoading(true);
    setError("");
    setResultImage(null);

    try {
      const formData = new FormData();
      formData.append("person_image", personImage);

      // Fetch the product image and send it as a file for maximum reliability
      const productImgUrl = product.image_reference || "";
      if (productImgUrl) {
        try {
          const imgResp = await fetch(productImgUrl);
          if (imgResp.ok) {
            const blob = await imgResp.blob();
            const ext = productImgUrl.split(".").pop() || "jpg";
            formData.append("product_image", blob, `product.${ext}`);
          } else {
            // Fallback: send the URL string instead
            formData.append("product_image_url", productImgUrl);
          }
        } catch {
          // Fallback: send the URL string instead
          formData.append("product_image_url", productImgUrl);
        }
      }

      const response = await fetch("http://localhost:8000/api/virtual-tryon", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setResultImage(data.image);
      } else {
        setError(
          data.error ||
            "Virtual try-on failed. Please try with a clearer full-body photo.",
        );
      }
    } catch (err) {
      console.error("Virtual try-on error:", err);
      setError(
        "Failed to connect to the virtual try-on service. Please try again.",
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setPersonImage(null);
    setPersonPreview(null);
    setResultImage(null);
    setError("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="vto-overlay" onClick={onClose}>
      <div className="vto-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="vto-header">
          <div className="vto-header-title">
            <span className="vto-header-icon">👗</span>
            <div>
              <h3>3D Virtual Trial Room</h3>
              <p className="vto-subtitle">Try on {product.product_name}</p>
            </div>
          </div>
          <button
            className="vto-close-btn"
            onClick={onClose}
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="vto-body">
          {/* Product preview (left side) */}
          <div className="vto-product-section">
            <div className="vto-section-label">Product</div>
            <div className="vto-product-preview">
              <img
                src={product.image_reference || "/images/placeholder.png"}
                alt={product.product_name}
                onError={(e) => {
                  e.target.src = "/images/placeholder.png";
                }}
              />
            </div>
            <div className="vto-product-name">{product.product_name}</div>
          </div>

          {/* Arrow / Plus indicator */}
          <div className="vto-plus-indicator">
            <span>+</span>
          </div>

          {/* Upload section (middle) */}
          <div className="vto-upload-section">
            <div className="vto-section-label">Your Photo</div>
            {!personPreview ? (
              <div
                className={`vto-dropzone ${dragActive ? "drag-active" : ""}`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <div className="vto-dropzone-icon">📸</div>
                <p className="vto-dropzone-text">
                  Drag & drop your full-body photo here
                </p>
                <p className="vto-dropzone-hint">or click to browse</p>
                <span className="vto-dropzone-formats">
                  JPG, PNG • Max 10MB
                </span>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleInputChange}
                  className="vto-file-input"
                />
              </div>
            ) : (
              <div className="vto-person-preview">
                <img src={personPreview} alt="Your photo" />
                <button
                  className="vto-change-photo-btn"
                  onClick={handleReset}
                  title="Change photo"
                >
                  🔄 Change
                </button>
              </div>
            )}
          </div>

          {/* Arrow indicator */}
          <div className="vto-arrow-indicator">
            <span>→</span>
          </div>

          {/* Result section (right) */}
          <div className="vto-result-section">
            <div className="vto-section-label">Try-On Result</div>
            <div className="vto-result-preview">
              {isLoading ? (
                <div className="vto-loading">
                  <div className="vto-spinner"></div>
                  <p>Generating your virtual try-on...</p>
                  <p className="vto-loading-hint">
                    This may take a few seconds
                  </p>
                </div>
              ) : resultImage ? (
                <img src={resultImage} alt="Virtual try-on result" />
              ) : (
                <div className="vto-result-placeholder">
                  <span className="vto-result-placeholder-icon">🪞</span>
                  <p>Your try-on result will appear here</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="vto-error">
            <span>⚠️</span> {error}
          </div>
        )}

        {/* Footer / Action */}
        <div className="vto-footer">
          <div className="vto-tips">
            <strong>💡 Tips:</strong> Use a clear, full-body photo with good
            lighting for best results.
          </div>
          <button
            className="vto-try-btn"
            onClick={handleTryOn}
            disabled={!personImage || isLoading}
          >
            {isLoading ? (
              <>
                <span className="vto-btn-spinner"></span> Generating...
              </>
            ) : resultImage ? (
              "🔄 Try Again"
            ) : (
              "✨ Try It On!"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
