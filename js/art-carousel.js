{ // block scope to prevent variable names interfering with other scripts
    let imgSrc, imgList, imgId;
    let carouselOpen = false;

document.addEventListener('DOMContentLoaded', function () {
    const images = document.querySelectorAll('#gallery img');
    imgList = Array.from(images);

    document.querySelector("#close").addEventListener('click', closeCarousel);

    images.forEach((img, index) => {
        img.setAttribute('draggable', 'false');
        img.addEventListener('click', () => setImage(index));
    });

    document.getElementById('carousel').addEventListener('click', function (event) {
        if (event.target.id === 'carousel' || event.target.id === 'close') {
            closeCarousel();
        }
    });
});

const displayImg = document.querySelector('#display-img');
//const display = document.querySelector('#display');
const imageNum = document.querySelector('#num');
const carousel = document.querySelector('#carousel');


    function setImage(id) {
        carouselOpen = true;
        if (id > imgList.length - 1) {
            imgId = 0;
        } else if (id < 0) {
            imgId = imgList.length - 1;
        } else {
            imgId = id;
        }

        imageNum.textContent = `${imgId + 1} / ${imgList.length}`;
        carousel.style.display = 'initial';

        const src = imgList[imgId].getAttribute('src');
        displayImg.setAttribute('src', src);
    }



function changeImg(iterator) {
    if (carouselOpen) {
        setImage(imgId + iterator);
    }
}

function closeCarousel() {
    carousel.style.display = 'none';
    carouselOpen = false;
}

document.addEventListener('keydown', function (e) {
    switch (e.key) {
        case 'ArrowLeft':
            changeImg(-1);
            break;

        case 'ArrowRight':
            changeImg(1);
            break;

        case 'Escape':
            closeCarousel();
            break;

        default:
            return; // Exit this handler for other keys
    }
    e.preventDefault(); // Prevent the default action (scroll / move caret)
});
}