document.addEventListener("DOMContentLoaded", function () {
  const paymentButton = document.getElementById('payment-button');
  const paymentPopup = document.getElementById('payment-popup');
  const paymentFrame = document.getElementById('payment-frame');
  const paymentWaiting = document.getElementById('payment-waiting');

  if (paymentButton) {
    paymentButton.addEventListener('click', function (e) {
      e.preventDefault();

      const amount = parseFloat("{{ '%.2f' % total }}");
      const specialKey = "heooeoweo2930";  // replace if dynamic
      const paymentUrl = `/paymentapi?amount=${amount}&specialkey=${specialKey}`;

      if (paymentFrame) paymentFrame.src = paymentUrl;
      if (paymentPopup) paymentPopup.classList.remove('hidden');
      if (paymentWaiting) paymentWaiting.classList.remove('hidden');

      const orderId = "{{ order_id }}";
      checkPaymentStatus(orderId);
    });
  }

  function checkPaymentStatus(orderId) {
    const interval = setInterval(() => {
      fetch(`/check_payment_status?order_id=${orderId}`)
        .then(res => res.json())
        .then(data => {
          if (data.status === "paid") {
            clearInterval(interval);
            if (paymentWaiting) paymentWaiting.classList.add('hidden');
            if (paymentPopup) paymentPopup.classList.add('hidden');
            window.location.href = `/track/${data.tracking}`;
          }
        });
    }, 10000);
  }
});




