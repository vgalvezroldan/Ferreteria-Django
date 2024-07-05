function formatearMoneda(valor, moneda = 'CLP') {
  return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: moneda
  }).format(valor);
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

function fetchWithCsrf(url, options = {}) {
    const headers = options.headers || {};
    headers['X-CSRFToken'] = csrftoken;

    options.headers = headers;
    return fetch(url, options);
}

function agregarAlCarrito(productoId) {
    const csrfTokenElement = document.querySelector('input[name="csrfmiddlewaretoken"]');
    const csrfToken = csrfTokenElement ? csrfTokenElement.value : '';

    if (!csrfToken) {
        console.error('CSRF token not found');
        return;
    }

    fetch(`/agregar_al_carrito/${productoId}/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
        },
        body: JSON.stringify({}),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("Network response was not ok");
        }
        return response.json();
    })
    .then(data => {
        // Mostrar la alerta de SweetAlert2
        Swal.fire({
            position: "top-end",
            icon: "success",
            title: "Producto agregado al carrito",
            showConfirmButton: false,
            timer: 1500
        });
        actualizarContadorCarrito(); // Actualizar el contador del carrito
    })
    .catch(error => {
        console.error("Error al agregar el producto al carrito:", error);
    });
}


// Función para cargar el carrito
document.addEventListener("DOMContentLoaded", function () { 
  var carritoModal = document.getElementById("carritoModal"); 
  carritoModal.addEventListener("show.bs.modal", function () { 
      cargarCarrito();
  });
  actualizarContadorCarrito(); // Actualizar el contador del carrito al cargar la página
});

function cargarCarrito() {
  fetch("/ver_carrito/") 
      .then(response => response.json()) 
      .then(data => {
          const modalBody = document.querySelector("#carritoModal .modal-body"); 
          modalBody.innerHTML = ""; 
          const irAPagarBtn = document.getElementById("irAPagarBtn");
          
          if (data.productos && data.productos.length > 0) { 
              data.productos.forEach(producto => { 
                  const productoDiv = document.createElement("div"); 
                  productoDiv.style.marginTop = "10px";
                  productoDiv.style.marginBottom = "10px";
                  productoDiv.innerHTML = `<h5 style="font-size: 2rem; font-weight: bold;">${producto.nombre}</h5>
                                           <p>Precio unitario: ${formatearMoneda(producto.precio)}</p>`; 
                  const cantidadInput = document.createElement("input"); 
                  cantidadInput.style.fontWeight = "bold";
                  cantidadInput.style.borderRadius = "5px";
                  cantidadInput.style.width = "80px";
                  cantidadInput.style.paddingLeft = "10px";
                  cantidadInput.style.paddingTop = "5px";
                  cantidadInput.style.paddingBottom = "5px";
                  cantidadInput.style.marginLeft = "15px";
                  cantidadInput.style.marginRight = "10px";
                  cantidadInput.style.border = "1px solid #5f5f5f";
                  cantidadInput.type = "number"; 
                  cantidadInput.value = producto.cantidad; 
                  cantidadInput.min = "1";
                  cantidadInput.max = producto.stock;
                  cantidadInput.addEventListener("change", () => {
                      actualizarCantidad(producto.id, cantidadInput.value);
                  });
                  const eliminarBtn = document.createElement("button"); 
                  eliminarBtn.style.color = "white";
                  eliminarBtn.style.fontWeight = "bold";
                  eliminarBtn.style.padding = "6px";
                  eliminarBtn.style.borderRadius = "5px";
                  eliminarBtn.style.border = "none";
                  eliminarBtn.style.backgroundColor = "#b42929";
                  eliminarBtn.textContent = "Eliminar"; 
                  eliminarBtn.addEventListener("click", () => eliminarProducto(producto.id)); 
                  productoDiv.appendChild(cantidadInput); 
                  productoDiv.appendChild(eliminarBtn); 
                  modalBody.appendChild(productoDiv); 
              });
              const totalElement = document.createElement("p"); 
              totalElement.id = "totalCarrito"; 
              totalElement.textContent = `Total: ${formatearMoneda(data.total)}`;
              modalBody.appendChild(totalElement); 
              irAPagarBtn.disabled = false; // Habilitar el botón si hay productos
          } else {
              modalBody.innerHTML = "<p>El carrito está vacío.</p>"; 
              irAPagarBtn.disabled = true; // Deshabilitar el botón si el carrito está vacío
          }
          actualizarContadorCarrito(); // Actualizar el contador del carrito después de cargar el carrito
      })
      .catch(error => console.error("Error al cargar el carrito:", error)); 
}

function actualizarCantidad(productoId, cantidad) {
  fetch(`/actualizar_carrito/${productoId}/`, { 
      method: "POST", 
      headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"), 
      },
      body: JSON.stringify({ cantidad: parseInt(cantidad) })  
  })
  .then(response => { 
      console.log('Respuesta del servidor:', response); 
      if (!response.ok) {
          return response.json().then(errorData => {
              throw new Error(errorData.mensaje);
          });
      }
      return response.json();
  })
  .then(data => {
      console.log('Datos recibidos:', data);
      const totalElement = document.getElementById("totalCarrito"); 
      if (totalElement) { 
          totalElement.textContent = `Total: ${formatearMoneda(data.totalCarrito)}`; 
      }
      cargarCarrito(); // Recargar el carrito para actualizar la interfaz
  })
  .catch(error => console.error("Error al actualizar la cantidad del producto:", error));
}

function eliminarProducto(productoId) {
    fetch(`/eliminar_del_carrito/${productoId}/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
        },
    })
    .then((response) => {
        if (!response.ok) {
            throw new Error('Network response was not ok.');
        }
        return response.json();
    })
    .then((data) => {
        Swal.fire({
            position: "top-end",
            icon: "error",
            title: "Producto eliminado del carrito",
            showConfirmButton: false,
            timer: 1500
        });
        cargarCarrito(); // Recargar el carrito para actualizar la interfaz
        actualizarContadorCarrito(); // Actualizar el contador del carrito
    })
    .catch((error) => {
        console.error("Error al eliminar el producto del carrito:", error);
    });
}


// Función para actualizar el contador del carrito
function actualizarContadorCarrito() {
  fetch("/ver_carrito/")
  .then(response => response.json())
  .then(data => {
      const cartCount = document.getElementById('cart-count');
      let totalItems = data.productos.reduce((acc, producto) => acc + producto.cantidad, 0); // Sumar las cantidades de todos los productos
      cartCount.textContent = totalItems;
  })
  .catch(error => console.error("Error al actualizar el contador del carrito:", error));
}

document.addEventListener("DOMContentLoaded", function () { 
  var carritoModal = document.getElementById("carritoModal"); 
  carritoModal.addEventListener("show.bs.modal", function () { 
      cargarCarrito(); 
  });
  var procederAlPagoBtn = document.getElementById("irAPagarBtn"); 
  procederAlPagoBtn.addEventListener("click", function () { 
      window.location.href = "/carrito/"; 
  });
  actualizarContadorCarrito(); // Actualizar el contador del carrito al cargar la página
});

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('registroForm');

    form.addEventListener('submit', function (event) {
        event.preventDefault();

        const formData = new FormData(form);
        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log('Response data:', data);  // Agregar para depuración
            if (data.success) {
                Swal.fire({
                    position: 'center',
                    icon: 'success',
                    title: 'Usuario registrado con éxito',
                    showConfirmButton: false,
                    timer: 3000 // Mostrar la alerta por 3 segundos
                });
                setTimeout(() => {
                    window.location.href = '/formulario_datos'; // Redirigir a la página deseada
                }, 3000); // Esperar 3 segundos antes de redirigir
            } else {
                let errorMessage = '';
                for (let field in data.errors) {
                    data.errors[field].forEach(error => {
                        errorMessage += `${error}<br>`;
                    });
                }
                Swal.fire({
                    position: 'center',
                    icon: 'error',
                    title: 'Errores en el formulario',
                    html: errorMessage,
                    showConfirmButton: false,
                    timer: 5000
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            Swal.fire({
                position: 'center',
                icon: 'error',
                title: 'Error en el servidor',
                text: 'Hubo un problema con la solicitud. Por favor, inténtalo de nuevo más tarde.',
                showConfirmButton: false,
                timer: 5000
            });
        });
    });
});

