import React, { useState, useEffect } from 'react';
import './App.css';

const App = () => {
  const [catImages, setCatImages] = useState([]);
  const [dogImages, setDogImages] = useState([]);
  const [countdown, setCountdown] = useState(60);
  const [totalImages, setTotalImages] = useState(0);

  const fetchImage = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8001/next-image/', {
        method: 'POST',
        mode: 'cors',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 403) {
          const errorData = await response.json();
          const waitSeconds = errorData.detail.wait_seconds;
          setCountdown(waitSeconds);
        } else {
          throw new Error('Network response was not ok');
        }
      } else {
        const data = await response.json();
        const { category, imageBase64 } = data;
        const timestamp = new Date().toLocaleTimeString();
        const newImage = { src: `data:image/jpeg;base64,${imageBase64}`, timestamp };

        if (category === 'cat') {
          setCatImages(prev => [newImage, ...prev].slice(0, 10));
        } else {
          setDogImages(prev => [newImage, ...prev].slice(0, 10));
        }

        setTotalImages(prevTotal => prevTotal + 1); // Update the total number of images retrieved
      }
    } catch (error) {
      console.error('Error fetching image:', error);
    }
  };

  useEffect(() => {
    const interval = setInterval(() => {
      setCountdown(prev => (prev === 0 ? 60 : prev - 1));
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (countdown === 0) {
      fetchImage();
    }
  }, [countdown]);

  useEffect(() => {
    fetchImage();
  }, []);

  return (
    <div className="App">
      <h1>Cat and Dog Images</h1>
      <div className="countdown">Next image in: {countdown} seconds</div>
      <div className="total-images">Total images retrieved: {totalImages}</div>
      <div className="image-columns">
        <div className="image-column">
          <h2>Cats</h2>
          {catImages.map((image, index) => (
            <div key={index} className="image-container">
              <img src={image.src} alt="cat" className="image" />
              <div className="timestamp">{image.timestamp}</div>
            </div>
          ))}
        </div>
        <div className="image-column">
          <h2>Dogs</h2>
          {dogImages.map((image, index) => (
            <div key={index} className="image-container">
              <img src={image.src} alt="dog" className="image" />
              <div className="timestamp">{image.timestamp}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default App;
