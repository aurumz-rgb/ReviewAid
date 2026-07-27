const toggleBtn = document.getElementById('theme-toggle');
const htmlElement = document.documentElement;

const currentTheme = localStorage.getItem('theme') || 'dark';
htmlElement.setAttribute('data-theme', currentTheme);

toggleBtn.addEventListener('click', () => {
  const existingTheme = htmlElement.getAttribute('data-theme');
  const newTheme = existingTheme === 'dark' ? 'light' : 'dark';

  htmlElement.setAttribute('data-theme', newTheme);
  localStorage.setItem('theme', newTheme);
});


window.addEventListener('scroll', reveal);

function reveal() {
  var reveals = document.querySelectorAll('.reveal');

  for (var i = 0; i < reveals.length; i++) {

    var windowHeight = window.innerHeight;
    var elementTop = reveals[i].getBoundingClientRect().top;
    var elementVisible = 150;

    if (elementTop < windowHeight - elementVisible) {
      reveals[i].classList.add('active');
    }
  }
}
reveal();



const lightbox = document.getElementById('lightbox');
const lightboxImg = document.getElementById('lightbox-img');
const closeBtn = document.getElementsByClassName('close-lightbox')[0];
const showcaseImages = document.querySelectorAll('.showcase-img');


showcaseImages.forEach(img => {
  img.addEventListener('click', function () {
    lightbox.style.display = 'flex';

    setTimeout(() => {
      lightbox.classList.add('show');
    }, 10);
    lightboxImg.src = this.src;
    document.body.style.overflow = 'hidden';
  });
});


function hideLightbox() {
  lightbox.classList.remove('show');
  setTimeout(() => {
    lightbox.style.display = 'none';
    lightboxImg.src = '';
    document.body.style.overflow = 'auto';
  }, 300);
}

closeBtn.addEventListener('click', hideLightbox);


lightbox.addEventListener('click', function (e) {
  if (e.target === lightbox) {
    hideLightbox();
  }
});


document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape' && lightbox.style.display === 'flex') {
    hideLightbox();
  }
});



const citations = {
  apa: "Sahu, V., & Balakrishnan, M. (2026). ReviewAid: An Open-Source Tool for Efficient PICO-Based Screening and Data Extraction in Systematic Reviews. Journal of Open Research Software, 14 (1), 21. https://doi.org/10.5334/jors.672",
  vancouver: "Sahu V, Balakrishnan M. ReviewAid: An Open-Source Tool for Efficient PICO-Based Screening and Data Extraction in Systematic Reviews. J Open Res Softw. 2026;14(1):21. doi:10.5334/jors.672",
  chicago: "Sahu, Vihaan, and Mohith Balakrishnan. 2026. \"ReviewAid: An Open-Source Tool for Efficient PICO-Based Screening and Data Extraction in Systematic Reviews.\" Journal of Open Research Software 14 (1): 21. https://doi.org/10.5334/jors.672.",
  harvard: "Sahu, V. and Balakrishnan, M. (2026) ‘ReviewAid: An Open-Source Tool for Efficient PICO-Based Screening and Data Extraction in Systematic Reviews’, Journal of Open Research Software, 14(1), p. 21. Available at: https://doi.org/10.5334/jors.672",
  mla: "Sahu, Vihaan, and Mohith Balakrishnan. \"ReviewAid: An Open-Source Tool for Efficient PICO-Based Screening and Data Extraction in Systematic Reviews.\" Journal of Open Research Software, vol. 14, no. 1, 2026, p. 21.",
  ieee: "V. Sahu and M. Balakrishnan, \"ReviewAid: An Open-Source Tool for Efficient PICO-Based Screening and Data Extraction in Systematic Reviews,\" Journal of Open Research Software, vol. 14, no. 1, p. 21, 2026. doi: 10.5334/jors.672."
};

const citationSelect = document.getElementById("citationType");
const citationText = document.getElementById("citationText");
const copyButton = document.getElementById("copyButton");


citationText.innerHTML = "<em>" + citations['apa'] + "</em>";

citationSelect.addEventListener("change", () => {
  const selected = citationSelect.value;
  citationText.innerHTML = "<em>" + citations[selected] + "</em>";
});

function copyCitation() {
  navigator.clipboard.writeText(citationText.innerText).then(() => {
    const originalHTML = copyButton.innerHTML;
    copyButton.innerHTML = "<span>Copied!</span>";
    copyButton.classList.remove('btn-primary');
    copyButton.classList.add('btn-secondary');

    setTimeout(() => {
      copyButton.innerHTML = originalHTML;
      copyButton.classList.remove('btn-secondary');
      copyButton.classList.add('btn-primary');
    }, 2000);
  });
}

copyButton.addEventListener("click", copyCitation);

function downloadCitation(format) {
  let content = "";
  let filename = "reviewaid_citation";

  if (format === 'ris') {
    content = `TY  - JOUR
T1  - ReviewAid: An Open-Source Tool for Efficient PICO-Based Screening and Data Extraction in Systematic Reviews
AU  - Sahu, V.
AU  - Balakrishnan, M.
JO  - Journal of Open Research Software
PY  - 2026
VL  - 14
IS  - 1
SP  - 21
DO  - 10.5334/jors.672
ER  - `;
    filename += ".ris";
  } else if (format === 'bibtex') {
    content = `@article{Sahu2026,
  author = {Sahu, V. and Balakrishnan, M.},
  title = {ReviewAid: An Open-Source Tool for Efficient PICO-Based Screening and Data Extraction in Systematic Reviews},
  journal = {Journal of Open Research Software},
  year = {2026},
  volume = {14},
  number = {1},
  pages = {21},
  doi = {10.5334/jors.672}
}`;
    filename += ".bib";
  }

  const blob = new Blob([content], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}