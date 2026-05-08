document.addEventListener('DOMContentLoaded', () => {
    // 1. Sayı Sayma Efekti (Dashboard için)
    const counters = document.querySelectorAll('.stat-value');
    counters.forEach(counter => {
        const target = parseInt(counter.innerText);
        if (isNaN(target)) return;
        
        let count = 0;
        const speed = 20; // Hız ayarı
        const increment = target / speed;

        const updateCount = () => {
            if (count < target) {
                count += increment;
                counter.innerText = Math.ceil(count);
                setTimeout(updateCount, 50);
            } else {
                counter.innerText = target;
            }
        };
        updateCount();
    });

    // 2. Rapor Çubukları Animasyonu
    const progressBars = document.querySelectorAll('.progress-fill');
    setTimeout(() => {
        progressBars.forEach(bar => {
            const percent = bar.getAttribute('data-width'); // HTML'de data-width="%70" olmalı
            bar.style.width = percent;
        });
    }, 300);

    // 3. Basit Tablo Arama (Hocaya gösterirsin, çok etkilenir)
    const searchInput = document.querySelector('.search-bar input');
    if (searchInput) {
        searchInput.addEventListener('keyup', (e) => {
            const term = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const text = row.innerText.toLowerCase();
                row.style.display = text.includes(term) ? '' : 'none';
            });
        });
    }
});