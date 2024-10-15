function fetchTodos(todoListId) {
    console.log(`Fetching todos for todo list ID: ${todoListId}`);
    const projectId = document.getElementById('project-select').value;
    fetch(`/todos/${projectId}/${todoListId}`)
        .then(response => {
            console.log('Response status:', response.status);
            console.log('Response headers:', Object.fromEntries(response.headers.entries()));
            return response.json();
        })
        .then(data => {
            console.log('Todos received:', data);
            populateTodosDropdown(data);
            displayTodos(data);
        })
        .catch(error => {
            console.error('Error fetching todos:', error);
            document.getElementById('todo-list').innerHTML = `<p>Error loading todos: ${error.message}</p>`;
            document.getElementById('todo-select').innerHTML = '<option value="">Error loading todos</option>';
        });
}

function populateTodosDropdown(todos) {
    const todoSelect = document.getElementById('todo-select');
    todoSelect.innerHTML = '<option value="">Select a todo</option>';
    
    todos.forEach(todo => {
        const option = document.createElement('option');
        option.value = todo.id;
        option.textContent = todo.title || 'Unnamed todo';
        todoSelect.appendChild(option);
    });
}

function displayTodos(todos) {
    const todoList = document.getElementById('todo-list');
    todoList.innerHTML = '';
    
    if (!Array.isArray(todos) || todos.length === 0) {
        todoList.innerHTML = '<p>No todos found.</p>';
        return;
    }

    todos.forEach(todo => {
        const todoItem = document.createElement('div');
        todoItem.textContent = todo.title || 'Unnamed todo';
        todoList.appendChild(todoItem);
    });
}

function onTodoListSelected(selectElement) {
    const selectedTodoListId = selectElement.value;
    console.log('Selected todo list ID:', selectedTodoListId);
    if (selectedTodoListId) {
        fetchTodos(selectedTodoListId);
    } else {
        document.getElementById('todo-select').innerHTML = '<option value="">Select a todo</option>';
        document.getElementById('todo-list').innerHTML = '';
    }
}
