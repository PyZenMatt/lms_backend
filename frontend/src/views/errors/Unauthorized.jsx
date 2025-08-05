import React from "react";

const Unauthorized = () => {
    return (
        <div style={{ textAlign: "center", marginTop: "50px" }}>
            <h1>Accesso Negato</h1>
            <p>Non hai i permessi per accedere a questa pagina.</p>
            <a href="/login" style={{ color: "blue", textDecoration: "underline" }}>
                Torna al Login
            </a>
        </div>
    );
};

export default Unauthorized;