const form = document.querySelector("form");

const fullname = document.getElementById("name");
const email = document.getElementById("email");
const phone = document.getElementById("phone");
const subject = document.getElementById("subject");
const mess = document.getElementById("message");

function sendEmail() {
    const bodyMessage = `Full Name: ${fullname.value}<br> Email: ${email.value}<br> Phone: ${phone.value}<br> Message: ${mess.value}<br>`;

    Email.send({
        SecureToken : "1be84deb-f223-4df6-a3e8-f2a500b0c88c",
        To : 'parkermiconi@gmail.com',
        From : "parkermiconi@gmail.com",
        Subject : subject.value,
        Body : bodyMessage
    }).then(
      message => alert("Application Submitted")
    );
}

form.addEventListener("submit", (e) => {
    e.preventDefault();

    sendEmail();
});